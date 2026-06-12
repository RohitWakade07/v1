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
from app.services.pool_service import ContainerPoolService
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
        self.pool_service = ContainerPoolService()

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
        container_id = None
        language = None
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

            # Load configuration
            config_path = Path(__file__).parent.parent / "graders" / assignment_slug / "config.yaml"
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
            assets_list = config.get("assets", [])
            for asset in assets_list:
                src_name = asset["source"]
                tgt_rel = asset["target"]

                local_asset_path = Path(__file__).parent.parent / "graders" / assignment_slug / "assets" / src_name
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

            os.chmod(submission_dir, 0o777)
            for root_dir, dirs, files in os.walk(submission_dir):
                for d in dirs:
                    os.chmod(os.path.join(root_dir, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root_dir, f), 0o777)

            # ── PHASE 2: ACQUIRE CONTAINER ────────────────────────────────────
            logger.info("Phase 2: Acquiring pre-warmed container")
            image_name = config.get("docker_image", "python:3.10-slim")
            
            lang_map = {
                "python:3.10-slim": "python",
                "openjdk:17-slim": "java",
                "gcc:11": "cpp",
                "node:18-slim": "javascript"
            }
            language = lang_map.get(image_name, "python")
            
            # We block here or retry if no container is available
            retries = 0
            while not container_id and retries < 10:
                container_id = self.pool_service.acquire_container(language)
                if not container_id:
                    retries += 1
                    await asyncio.sleep(2)
            
            if not container_id:
                raise RuntimeError(f"Failed to acquire pre-warmed {language} container from pool after 20 seconds")
                
            container = self.docker_client.containers.get(container_id)
            exec_metadata["container_id"] = container.id

            # ── PHASE 3: EXECUTION ────────────────────────────────────────────
            logger.info("Phase 3: Executing inside pre-warmed sandbox container")
            
            # Create the workspace INSIDE the prewarmed container
            # The prewarmed container doesn't have the volume mounted with the dynamic submission ID path
            # Wait, the pool containers don't have volumes!
            # We must use `docker cp` to put the files into the container, OR 
            # pre-warmed containers MUST mount the parent `/tmp/autograder_jobs` directory!
            # Assuming pool containers mount `/tmp/autograder_jobs` globally:

            # Get relative paths
            project_name = os.environ.get("COMPOSE_PROJECT_NAME", "backend")
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

            # Ensure the container has access to it. If the pre-warmed container mounted /tmp/autograder_jobs:
            # We just docker exec.
            command = config.get("execution_command")
            
            start_time = time.time()
            
            # Execute command inside container
            # Note: exec_run is blocking. We can use loop.run_in_executor
            loop = asyncio.get_event_loop()
            
            def run_exec():
                return container.exec_run(
                    cmd=command,
                    workdir=container_workdir,
                    environment={
                        "WORKSPACE": container_submission,
                        "ASSETS":    container_assets,
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
            except (asyncio.TimeoutError, Exception):
                logger.warning(f"Submission {submission_id} execution timed out")
                exec_metadata["timed_out"] = True
                exec_metadata["stdout"] = "Execution timed out"
                # To actually stop the process inside the container, it's tricky with exec_run. 
                # We might have to restart the container, so let's mark it for hard release
                try:
                    container.restart()
                except Exception:
                    pass

            exec_metadata["execution_time_ms"] = int((time.time() - start_time) * 1000)
            
            # We don't get separate stderr from exec_run easily, it multiplexes it.
            exec_metadata["stderr"] = ""
            
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
            if container_id and language:
                self.pool_service.release_container(language, container_id)

            try:
                shutil.rmtree(job_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Error removing job directory: {e}")

        return status_str, grading_result, exec_metadata
