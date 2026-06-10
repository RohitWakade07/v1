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


class DockerExecutor:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.docker_client = None

    async def execute(
        self,
        submission_id: str,
        assignment_slug: str,
        source_type: str,
        repo_url: str | None,
        zip_object_key: str | None,
    ) -> tuple[str, GradingResult, dict]:
        """
        Runs the full 5-phase execution lifecycle.
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
                        # Resolve the destination path and verify it stays inside submission_dir
                        dest = (submission_dir / member).resolve()
                        if not str(dest).startswith(str(submission_dir.resolve())):
                            raise ValueError(f"Path traversal detected in ZIP archive: {member}")
                    archive.extractall(path=submission_dir)
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

            # Load configuration
            config_path = Path(__file__).parent.parent / "graders" / assignment_slug / "config.yaml"
            if not config_path.exists():
                raise ValueError(f"No config.yaml found for assignment slug: {assignment_slug}")

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            exec_metadata["execution_command"] = config.get("execution_command", "")

            # Inject hidden assets
            logger.info("Injecting hidden assets")
            assets_list = config.get("assets", [])
            for asset in assets_list:
                src_name = asset["source"]
                tgt_rel = asset["target"]

                # We copy from local graders directory if available
                local_asset_path = Path(__file__).parent.parent / "graders" / assignment_slug / "assets" / src_name
                if local_asset_path.exists():
                    # Copy to assets_dir
                    temp_asset_dest = assets_dir / src_name
                    if local_asset_path.is_dir():
                        shutil.copytree(local_asset_path, temp_asset_dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(local_asset_path, temp_asset_dest)

                # Inject into submission workspace at target path
                target_dest = submission_dir / tgt_rel
                target_dest.parent.mkdir(parents=True, exist_ok=True)
                if local_asset_path.is_dir():
                    shutil.copytree(local_asset_path, target_dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(local_asset_path, target_dest)

            # NOTE: If the submission includes a requirements.txt, package
            # installation happens INSIDE the Docker container via the
            # execution command or a wrapper entrypoint — never on the host.

            # Make entry point scripts executable and give sandbox user write access
            os.chmod(submission_dir, 0o777)
            for root_dir, dirs, files in os.walk(submission_dir):
                for d in dirs:
                    os.chmod(os.path.join(root_dir, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root_dir, f), 0o777)

            # ── PHASE 2: VALIDATION ───────────────────────────────────────────
            logger.info("Phase 2: Validating submission structure and environment")
            # Image check
            image_name = config.get("docker_image")
            if not self.docker_client:
                raise RuntimeError("Docker client not connected")

            try:
                self.docker_client.images.get(image_name)
            except docker.errors.ImageNotFound:
                logger.info(f"Image {image_name} not found locally, pulling...")
                self.docker_client.images.pull(image_name)

            # ── PHASE 3: EXECUTION ────────────────────────────────────────────
            logger.info("Phase 3: Spawning Docker sandbox container")
            volumes = {
                str(submission_dir): {"bind": "/workspace/submission", "mode": "rw"},
                str(assets_dir):     {"bind": "/workspace/assets",     "mode": "ro"},
            }

            # Support optional working_dir relative to /workspace/submission
            container_workdir = "/workspace/submission"
            if config.get("working_dir"):
                container_workdir = f"/workspace/submission/{config['working_dir']}"

            container = self.docker_client.containers.run(
                image=image_name,
                command=config.get("execution_command"),
                name=f"grader-{uuid.uuid4().hex[:16]}",
                volumes=volumes,
                working_dir=container_workdir,
                environment={
                    "WORKSPACE": "/workspace/submission",
                    "ASSETS":    "/workspace/assets",
                },
                network_disabled=config.get("network_disabled", True),
                mem_limit=f"{config.get('memory_limit_mb', 512)}m",
                nano_cpus=int(config.get("cpu_limit", 1.0) * 1e9),
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                user="1000:1000",
                read_only=False,
                remove=False,
                detach=True,
                stdout=True,
                stderr=True,
            )

            exec_metadata["container_id"] = container.id
            start_time = time.time()

            # Wait for execution with proper timeout
            timeout = config.get("timeout_seconds", 60)
            loop = asyncio.get_event_loop()
            try:
                # container.wait() blocks until container exits; run in executor
                # with asyncio.wait_for() for a real execution timeout
                wait_result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: container.wait(timeout=timeout + 5)),
                    timeout=timeout,
                )
                exec_metadata["exit_code"] = wait_result.get("StatusCode", 1)
            except (asyncio.TimeoutError, Exception):
                logger.warning(f"Submission {submission_id} execution timed out")
                exec_metadata["timed_out"] = True
                try:
                    container.kill()
                except Exception:
                    pass

            exec_metadata["execution_time_ms"] = int((time.time() - start_time) * 1000)

            # Extract logs
            stdout_logs = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr_logs = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            exec_metadata["stdout"] = stdout_logs
            exec_metadata["stderr"] = stderr_logs

            container.reload()
            exec_metadata["oom_killed"] = container.attrs.get("State", {}).get("OOMKilled", False)

            # ── PHASE 4: GRADING ──────────────────────────────────────────────
            logger.info("Phase 4: Running grader checks")
            GraderClass = get_grader(assignment_slug)
            grader_config = {
                "execution_result": exec_metadata,
            }
            grader = GraderClass(
                workspace=str(submission_dir),
                assets_path=str(assets_dir),
                config=grader_config,
            )
            grading_result = grader.grade()
            status_str = "COMPLETED"

        except Exception as e:
            logger.exception(f"Job execution failed: {e}")
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
            logger.info("Phase 5: Cleaning up containers and workspace directories")
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.error(f"Error removing container: {e}")

            try:
                shutil.rmtree(job_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Error removing job directory: {e}")

        return status_str, grading_result, exec_metadata
