import asyncio
import logging
import os
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any

import docker
import yaml

from app.core.config import settings
from app.services.storage_service import StorageService
from graders.registry import get_grader
from graders.base_grader import GradingResult

logger = logging.getLogger(__name__)

# ── Docker client — lazy loaded at first use, not at import time ──────────────
# This prevents the API service from crashing on import when Docker socket
# is not available (API doesn't need Docker — only the worker does).
_docker_client = None

def get_docker_client():
    global _docker_client
    if _docker_client is None:
        logger.info("[DOCKER:INIT] Connecting to Docker daemon via environment config (or default unix socket)")
        _docker_client = docker.from_env()
        version = _docker_client.version()
        logger.info(f"[DOCKER:INIT] Connected — Docker version={version.get('Version')} API={version.get('ApiVersion')}")
    return _docker_client


# Image name → language slug mapping
_IMAGE_TO_LANGUAGE = {
    "python:3.10-slim": "python",
    "openjdk:17-slim":  "java",
    "gcc:11":           "cpp",
    "node:18-slim":     "javascript",
    "bash:5":           "bash",
}


def run_fresh_container(language: str, image_name: str) -> Any:
    container_name = f"grader-{language}-{uuid.uuid4().hex[:12]}"
    logger.info(f"[CONTAINER:SPAWN] image={image_name} name={container_name} language={language}")

    volume_name = os.environ.get("GRADER_VOLUME_NAME", "backend_grader_jobs")
    container = get_docker_client().containers.run(
        image=image_name,
        command="tail -f /dev/null",
        name=container_name,
        user="nobody",
        network_disabled=True,
        mem_limit="256m",
        memswap_limit="256m",
        cpu_quota=50000,
        cpu_period=100000,
        pids_limit=64,
        read_only=True,
        tmpfs={"/tmp": "size=128m,noexec"},
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        volumes={
            volume_name: {"bind": "/tmp/autograder_jobs", "mode": "rw"},
        },
        detach=True,
    )
    logger.info(f"[CONTAINER:SPAWN] Container started: id={container.id[:12]} name={container_name} status={container.status}")
    return container


def cleanup_container(container: Any) -> None:
    if not container:
        logger.debug("[CONTAINER:CLEANUP] No container to clean up — skipping")
        return
    cid = container.id[:12] if container.id else "unknown"
    try:
        logger.info(f"[CONTAINER:CLEANUP] Stopping container id={cid}")
        container.stop(timeout=5)
        logger.info(f"[CONTAINER:CLEANUP] Stopped container id={cid}")
    except Exception as e:
        logger.warning(f"[CONTAINER:CLEANUP] Stop failed for id={cid}: {e}")
    try:
        container.remove(force=True)
        logger.info(f"[CONTAINER:CLEANUP] Removed container id={cid}")
    except Exception as e:
        logger.warning(f"[CONTAINER:CLEANUP] Remove failed for id={cid}: {e}")


class DockerExecutor:

    async def execute(
        self,
        submission_id: str,
        assignment_slug: str,
        source_type: str,
        repo_url: str | None,
        zip_object_key: str | None,
    ) -> tuple[str, GradingResult, dict]:

        logger.info(
            f"[EXECUTOR:START] submission_id={submission_id} "
            f"slug={assignment_slug} source_type={source_type} "
            f"zip_key={zip_object_key} repo_url={repo_url}"
        )

        container      = None
        job_dir        = Path("/tmp/autograder_jobs") / submission_id
        submission_dir = job_dir / "submission"
        assets_dir     = job_dir / "assets"
        results_dir    = job_dir / "results"
        logs_dir       = job_dir / "logs"

        exec_metadata = {
            "stdout": "", "stderr": "", "execution_command": "",
            "exit_code": -1, "execution_time_ms": 0,
            "timed_out": False, "oom_killed": False,
            "container_id": "", "grader_logs": "",
        }

        try:
            # ── PHASE 1: PREPARATION ──────────────────────────────────────────
            logger.info(f"[PHASE1:PREP] submission_id={submission_id} job_dir={job_dir}")
            shutil.rmtree(job_dir, ignore_errors=True)
            submission_dir.mkdir(parents=True, exist_ok=True)
            assets_dir.mkdir(parents=True, exist_ok=True)
            results_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[PHASE1:PREP] Directories created")

            storage_service = StorageService()

            if source_type == "zip":
                if not zip_object_key:
                    raise ValueError("Missing zip_object_key for zip source type")

                zip_path = job_dir / "submission.zip"
                logger.info(f"[PHASE1:DOWNLOAD] Downloading ZIP key={zip_object_key}")
                t0 = time.time()
                await storage_service.download_file(
                    storage_service.bucket_submissions, zip_object_key, str(zip_path)
                )
                zip_size = zip_path.stat().st_size
                logger.info(f"[PHASE1:DOWNLOAD] Done in {int((time.time()-t0)*1000)}ms size={zip_size} bytes")

                logger.info(f"[PHASE1:EXTRACT] Extracting ZIP to {submission_dir}")
                with zipfile.ZipFile(zip_path, "r") as archive:
                    members = archive.namelist()
                    logger.debug(f"[PHASE1:EXTRACT] ZIP has {len(members)} entries: {members[:10]}")
                    for member in members:
                        dest = (submission_dir / member).resolve()
                        if not str(dest).startswith(str(submission_dir.resolve())):
                            raise ValueError(f"Path traversal detected: {member}")
                    archive.extractall(path=submission_dir)
                logger.info(f"[PHASE1:EXTRACT] Extraction complete")

                flatten_count = 0
                while True:
                    items = list(submission_dir.iterdir())
                    if len(items) == 1 and items[0].is_dir():
                        top_dir = items[0]
                        logger.info(f"[PHASE1:FLATTEN] Flattening: {top_dir.name}")
                        for child in top_dir.iterdir():
                            shutil.move(str(child), str(submission_dir / child.name))
                        top_dir.rmdir()
                        flatten_count += 1
                    else:
                        break
                if flatten_count:
                    logger.info(f"[PHASE1:FLATTEN] Flattened {flatten_count} level(s)")

                final_items = [p.name for p in submission_dir.iterdir()]
                logger.info(f"[PHASE1:CONTENTS] submission_dir has {len(final_items)} items: {final_items}")

            elif source_type == "github":
                if not repo_url:
                    raise ValueError("Missing repo_url for github source type")
                logger.info(f"[PHASE1:GIT] Cloning {repo_url}")
                t0 = time.time()
                cmd = ["git", "clone", "--depth=1", repo_url, str(submission_dir)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                elapsed = int((time.time() - t0) * 1000)
                if proc.returncode != 0:
                    logger.error(f"[PHASE1:GIT] Clone FAILED rc={proc.returncode} stderr={stderr.decode()[:500]}")
                    raise RuntimeError(f"Git clone failed: {stderr.decode()}")
                logger.info(f"[PHASE1:GIT] Clone OK in {elapsed}ms")
            else:
                raise ValueError(f"Unknown source type: {source_type}")

            # ── Load config ────────────────────────────────────────────────
            config_path = Path(__file__).parent.parent / "graders" / assignment_slug / "config.yaml"
            logger.info(f"[PHASE1:CONFIG] Loading {config_path}")
            if not config_path.exists():
                raise ValueError(f"No config.yaml found for slug: {assignment_slug}")

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(
                f"[PHASE1:CONFIG] docker_image={config.get('docker_image')} "
                f"cmd={config.get('execution_command')!r} "
                f"timeout={config.get('timeout_seconds')}s "
                f"target_file={config.get('target_file')} "
                f"assets={len(config.get('assets', []))}"
            )

            target_file = config.get("target_file")
            if target_file:
                found_paths = list(submission_dir.rglob(target_file))
                if found_paths:
                    submission_dir = found_paths[0].parent
                    logger.info(f"[PHASE1:TARGET] Found {target_file} — workspace → {submission_dir}")
                else:
                    logger.warning(f"[PHASE1:TARGET] {target_file} NOT FOUND under {submission_dir}")

            exec_metadata["execution_command"] = config.get("execution_command", "")

            # ── Inject assets ──────────────────────────────────────────────
            assets_list = config.get("assets", [])
            logger.info(f"[PHASE1:ASSETS] Injecting {len(assets_list)} asset(s)")
            for asset in assets_list:
                src_name = asset["source"]
                tgt_rel  = asset["target"]
                local_asset_path = Path(__file__).parent.parent / "graders" / assignment_slug / "assets" / src_name
                logger.debug(f"[PHASE1:ASSETS] {src_name} → {tgt_rel} exists={local_asset_path.exists()}")
                if local_asset_path.exists():
                    temp_asset_dest = assets_dir / src_name
                    if local_asset_path.is_dir():
                        shutil.copytree(local_asset_path, temp_asset_dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(local_asset_path, temp_asset_dest)
                target_dest = submission_dir / tgt_rel
                target_dest.parent.mkdir(parents=True, exist_ok=True)
                if local_asset_path.is_dir():
                    shutil.copytree(local_asset_path, target_dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(local_asset_path, target_dest)

            # ── Permissions ────────────────────────────────────────────────
            logger.info(f"[PHASE1:PERMS] Setting 0o777 on workspace")
            os.chmod(submission_dir, 0o777)
            for root_dir, dirs, files in os.walk(submission_dir):
                for d in dirs:
                    os.chmod(os.path.join(root_dir, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root_dir, f), 0o777)
            logger.info(f"[PHASE1:PERMS] Done")

            # ── PHASE 2: SPIN UP CONTAINER ────────────────────────────────────
            image_name = config.get("docker_image", "python:3.10-slim")
            language   = _IMAGE_TO_LANGUAGE.get(image_name, "generic")
            logger.info(f"[PHASE2:CONTAINER] Requesting container image={image_name} language={language}")
            t0 = time.time()
            container = run_fresh_container(language, image_name)
            exec_metadata["container_id"] = container.id
            logger.info(f"[PHASE2:CONTAINER] Ready in {int((time.time()-t0)*1000)}ms id={container.id[:12]}")

            # ── PHASE 3: EXECUTION ────────────────────────────────────────────
            job_rel             = str(Path(submission_id))
            base_submission     = job_dir / "submission"
            rel_path            = submission_dir.relative_to(base_submission)
            submission_vol_path = f"{job_rel}/submission"
            if str(rel_path) != ".":
                submission_vol_path = f"{job_rel}/submission/{rel_path}".replace("\\", "/")

            container_submission = f"/tmp/autograder_jobs/{submission_vol_path}"
            container_assets     = f"/tmp/autograder_jobs/{job_rel}/assets"
            container_workdir    = container_submission
            if config.get("working_dir"):
                container_workdir = f"{container_submission}/{config['working_dir']}"

            command = config.get("execution_command")
            timeout = config.get("timeout_seconds", 60)

            logger.info(
                f"[PHASE3:EXEC] cmd={command!r} workdir={container_workdir} timeout={timeout}s"
            )

            loop = asyncio.get_running_loop()
            start_time = time.time()

            def run_exec():
                return container.exec_run(
                    cmd=command,
                    workdir=container_workdir,
                    environment={"WORKSPACE": container_submission, "ASSETS": container_assets},
                    user="1000:1000",
                )

            try:
                exec_result = await asyncio.wait_for(
                    loop.run_in_executor(None, run_exec),
                    timeout=timeout,
                )
                elapsed_ms = int((time.time() - start_time) * 1000)
                exec_metadata["exit_code"] = exec_result.exit_code
                exec_metadata["stdout"]    = exec_result.output.decode("utf-8", errors="replace")
                logger.info(
                    f"[PHASE3:EXEC] Done in {elapsed_ms}ms "
                    f"exit_code={exec_result.exit_code} "
                    f"stdout_len={len(exec_metadata['stdout'])}"
                )
                logger.debug(f"[PHASE3:EXEC] stdout:\n{exec_metadata['stdout'][:1000]}")

            except asyncio.TimeoutError:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"[PHASE3:EXEC] TIMEOUT after {elapsed_ms}ms (limit={timeout}s)")
                exec_metadata["timed_out"] = True
                exec_metadata["stdout"]    = f"Execution timed out after {timeout}s"

            except Exception as exc:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error(f"[PHASE3:EXEC] EXCEPTION after {elapsed_ms}ms: {type(exc).__name__}: {exc}", exc_info=True)
                exec_metadata["stdout"] = f"Execution error: {exc}"

            exec_metadata["execution_time_ms"] = int((time.time() - start_time) * 1000)
            exec_metadata["stderr"] = ""

            # ── PHASE 4: GRADING ──────────────────────────────────────────────
            logger.info(f"[PHASE4:GRADE] Running grader slug={assignment_slug}")
            GraderClass    = get_grader(assignment_slug)
            logger.info(f"[PHASE4:GRADE] Grader={GraderClass.__name__}")
            grader         = GraderClass(
                workspace=str(submission_dir),
                assets_path=str(assets_dir),
                config={"execution_result": exec_metadata},
            )
            grading_result = grader.grade()

            logger.info(
                f"[PHASE4:GRADE] score={grading_result.score}/{grading_result.max_score} "
                f"passed={grading_result.passed} checks={len(grading_result.checks)}"
            )
            for i, check in enumerate(grading_result.checks):
                logger.info(
                    f"[PHASE4:GRADE] check[{i}] {check.name!r} "
                    f"passed={check.passed} marks={check.marks}/{check.max_marks} "
                    f"reason={check.reason!r}"
                )

            status_str = "COMPLETED"

        except Exception as e:
            logger.exception(f"[EXECUTOR:ERROR] FAILED submission_id={submission_id}: {type(e).__name__}: {e}")
            status_str = "FAILED"
            grading_result = GradingResult(
                score=0.0, max_score=5.0, passed=False, checks=[],
                feedback=f"Execution error: {str(e)}",
            )
            exec_metadata["grader_logs"] = f"Grader failed: {e}"

        finally:
            logger.info(f"[PHASE5:CLEANUP] Starting cleanup submission_id={submission_id}")
            cleanup_container(container)
            try:
                shutil.rmtree(job_dir, ignore_errors=True)
                logger.info(f"[PHASE5:CLEANUP] job_dir removed: {job_dir}")
            except Exception as e:
                logger.error(f"[PHASE5:CLEANUP] Failed to remove job_dir: {e}")

        logger.info(f"[EXECUTOR:DONE] submission_id={submission_id} status={status_str}")
        return status_str, grading_result, exec_metadata
