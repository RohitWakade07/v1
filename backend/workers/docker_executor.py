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

# Docker client lazy loaded — always use the mounted socket directly, no DOCKER_HOST env var
_docker_client = None

def get_docker_client():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    return _docker_client

# Image name → language slug mapping
_IMAGE_TO_LANGUAGE = {
    "python:3.10-slim": "python",
    "openjdk:17-slim": "java",
    "gcc:11": "cpp",
    "node:18-slim": "javascript",
    "bash:5": "bash",
}


def run_fresh_container(language: str, image_name: str) -> Any:
    """Spin up a fresh, security-hardened container for a single submission.

    Args:
        language: Language slug (used for naming only).
        image_name: Docker image to use (e.g. "python:3.10-slim").

    Returns:
        A running docker container object.
    """
    return get_docker_client().containers.run(
        image=image_name,
        command="tail -f /dev/null",  # Keep alive so exec_run can be called into it
        name=f"grader-{language}-{uuid.uuid4().hex[:12]}",
        # ── Security hardening ──────────────────────────────────────────────
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
        # ── Workspace volume ────────────────────────────────────────────────
        volumes={
            "grader_jobs": {"bind": "/tmp/autograder_jobs", "mode": "rw"},
        },
        detach=True,
    )


def cleanup_container(container: Any) -> None:
    """Stop and remove a container. Never raises — safe to call in finally blocks.

    Args:
        container: Docker container object returned by run_fresh_container.
    """
    if not container:
        return
    try:
        container.stop(timeout=5)
    except Exception:
        pass
    try:
        container.remove(force=True)
        logger.info(f"Cleaned up container {container.id}")
    except Exception as e:
        logger.warning(f"Could not remove container: {e}")


class DockerExecutor:
    """Runs the full 5-phase grading lifecycle for a single submission."""

    async def execute(
        self,
        submission_id: str,
        assignment_slug: str,
        source_type: str,
        repo_url: str | None,
        zip_object_key: str | None,
    ) -> tuple[str, GradingResult, dict]:
        """Run fetch → prepare → execute → grade → cleanup.

        Returns:
            tuple[status, grading_result, exec_metadata]
        """
        container = None
        job_dir = Path("/tmp/autograder_jobs") / submission_id
        submission_dir = job_dir / "submission"
        assets_dir = job_dir / "assets"
        results_dir = job_dir / "results"
        logs_dir = job_dir / "logs"

        exec_metadata = {
            "stdout": "",
            "stderr": "",
            "execution_command": "",
            "exit_code": -1,
            "execution_time_ms": 0,
            "timed_out": False,
            "oom_killed": False,
            "container_id": "",
            "grader_logs": "",
        }

        try:
            # ── PHASE 1: PREPARATION ──────────────────────────────────────────
            logger.info(f"Phase 1: Preparing directories for job {submission_id}")
            shutil.rmtree(job_dir, ignore_errors=True)
            submission_dir.mkdir(parents=True, exist_ok=True)
            assets_dir.mkdir(parents=True, exist_ok=True)
            results_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)

            storage_service = StorageService()

            if source_type == "zip":
                if not zip_object_key:
                    raise ValueError("Missing zip_object_key for zip source type")
                zip_path = job_dir / "submission.zip"
                logger.info(f"Downloading ZIP submission from key {zip_object_key}")
                await storage_service.download_file(
                    storage_service.bucket_submissions, zip_object_key, str(zip_path)
                )

                logger.info("Extracting ZIP archive safely")
                with zipfile.ZipFile(zip_path, "r") as archive:
                    for member in archive.namelist():
                        dest = (submission_dir / member).resolve()
                        if not str(dest).startswith(str(submission_dir.resolve())):
                            raise ValueError(f"Path traversal detected in ZIP archive: {member}")
                    archive.extractall(path=submission_dir)

                # Flatten single-directory nesting
                while True:
                    items = list(submission_dir.iterdir())
                    if len(items) == 1 and items[0].is_dir():
                        top_dir = items[0]
                        logger.info(f"Flattening nested directory: {top_dir.name}")
                        for child in top_dir.iterdir():
                            shutil.move(str(child), str(submission_dir / child.name))
                        top_dir.rmdir()
                    else:
                        break

            elif source_type == "github":
                if not repo_url:
                    raise ValueError("Missing repo_url for github source type")
                logger.info(f"Cloning github repository: {repo_url}")
                cmd = ["git", "clone", "--depth=1", repo_url, str(submission_dir)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {stderr.decode()}")
            else:
                raise ValueError(f"Unknown source type: {source_type}")

            # Load grader config
            config_path = (
                Path(__file__).parent.parent / "graders" / assignment_slug / "config.yaml"
            )
            if not config_path.exists():
                raise ValueError(f"No config.yaml found for assignment slug: {assignment_slug}")

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            target_file = config.get("target_file")
            if target_file:
                found_paths = list(submission_dir.rglob(target_file))
                if found_paths:
                    submission_dir = found_paths[0].parent
                    logger.info(f"Target {target_file} found. Updated workspace to {submission_dir}")

            exec_metadata["execution_command"] = config.get("execution_command", "")

            # Inject hidden assets
            logger.info("Injecting hidden assets")
            for asset in config.get("assets", []):
                src_name = asset["source"]
                tgt_rel = asset["target"]
                local_asset_path = (
                    Path(__file__).parent.parent / "graders" / assignment_slug / "assets" / src_name
                )
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

            # Make submission files world-readable for the nobody user inside the container
            os.chmod(submission_dir, 0o777)
            for root_dir, dirs, files in os.walk(submission_dir):
                for d in dirs:
                    os.chmod(os.path.join(root_dir, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root_dir, f), 0o777)

            # ── PHASE 2: SPIN UP FRESH CONTAINER ─────────────────────────────
            image_name = config.get("docker_image", "python:3.10-slim")
            language = _IMAGE_TO_LANGUAGE.get(image_name, "python")
            logger.info(f"Phase 2: Spinning up fresh container ({image_name})")

            container = run_fresh_container(language, image_name)
            exec_metadata["container_id"] = container.id

            # ── PHASE 3: EXECUTION ────────────────────────────────────────────
            logger.info("Phase 3: Executing inside sandbox container")

            job_rel = str(Path(submission_id))
            base_submission_dir = job_dir / "submission"
            rel_path = submission_dir.relative_to(base_submission_dir)
            submission_vol_path = f"{job_rel}/submission"
            if str(rel_path) != ".":
                submission_vol_path = f"{job_rel}/submission/{rel_path}".replace("\\", "/")

            assets_vol_path = f"{job_rel}/assets"
            container_submission = f"/tmp/autograder_jobs/{submission_vol_path}"
            container_assets = f"/tmp/autograder_jobs/{assets_vol_path}"
            container_workdir = container_submission
            if config.get("working_dir"):
                container_workdir = f"{container_submission}/{config['working_dir']}"

            command = config.get("execution_command")
            start_time = time.time()

            loop = asyncio.get_event_loop()

            def run_exec():
                return container.exec_run(
                    cmd=command,
                    workdir=container_workdir,
                    environment={
                        "WORKSPACE": container_submission,
                        "ASSETS": container_assets,
                    },
                    user="1000:1000",
                )

            timeout = config.get("timeout_seconds", 60)
            try:
                exec_result = await asyncio.wait_for(
                    loop.run_in_executor(None, run_exec),
                    timeout=timeout,
                )
                exec_metadata["exit_code"] = exec_result.exit_code
                exec_metadata["stdout"] = exec_result.output.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                logger.warning(f"Submission {submission_id} execution timed out after {timeout}s")
                exec_metadata["timed_out"] = True
                exec_metadata["stdout"] = "Execution timed out"
            except Exception as exc:
                logger.warning(f"exec_run failed for {submission_id}: {exc}")
                exec_metadata["stdout"] = f"Execution error: {exc}"

            exec_metadata["execution_time_ms"] = int((time.time() - start_time) * 1000)
            exec_metadata["stderr"] = ""

            # ── PHASE 4: GRADING ──────────────────────────────────────────────
            logger.info("Phase 4: Running grader checks")
            GraderClass = get_grader(assignment_slug)
            grader = GraderClass(
                workspace=str(submission_dir),
                assets_path=str(assets_dir),
                config={"execution_result": exec_metadata},
            )
            grading_result = grader.grade()
            status_str = "COMPLETED"

        except Exception as e:
            logger.exception(f"Job execution failed for {submission_id}: {e}")
            status_str = "FAILED"
            grading_result = GradingResult(
                score=0.0,
                max_score=5.0,
                passed=False,
                checks=[],
                feedback=f"Execution error: {str(e)}",
            )
            exec_metadata["grader_logs"] = f"Grader failed: {e}"

        finally:
            # ── PHASE 5: CLEANUP ──────────────────────────────────────────────
            logger.info("Phase 5: Cleaning up container and workspace")
            cleanup_container(container)
            try:
                shutil.rmtree(job_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Error removing job directory {job_dir}: {e}")

        return status_str, grading_result, exec_metadata
