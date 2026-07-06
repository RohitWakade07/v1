import os
import uuid
import time
import docker
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Submission
from workers.docker_executor import prepare_submission_directory

_docker_client = None

def get_docker_client():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client

async def start_sandbox(submission: Submission) -> dict:
    """
    Sets up a workspace for the submission and starts a sleeping Docker container.
    """
    job_id = f"sandbox-{uuid.uuid4()}"
    client = get_docker_client()
    
    # 1. Prepare submission directory (re-using the logic from docker_executor)
    job_dir = Path("/autograder_jobs") / job_id
    submission_dir = job_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)
    
    # The signature in docker_executor is:
    # def prepare_submission_directory(source_type, repository_url, github_token, commit_hash, zip_url, job_dir):
    await asyncio.to_thread(
        prepare_submission_directory,
        submission.source_type.value,
        submission.repository_url,
        submission.github_token,
        submission.commit_hash,
        submission.zip_url,
        job_dir
    )

    # 2. Start Docker container
    image_name = "grader-python:latest"
    container_name = f"mentor-sandbox-{job_id}"
    volume_name = os.environ.get("GRADER_VOLUME_NAME", "backend_grader_jobs")

    container = client.containers.run(
        image=image_name,
        command="tail -f /dev/null",
        name=container_name,
        user="root",
        network_disabled=False,
        mem_limit="512m",
        memswap_limit="512m",
        cpu_quota=100000,
        cpu_period=100000,
        detach=True,
        tty=True,
        stdin_open=True,
        volumes={
            volume_name: {"bind": "/autograder_jobs", "mode": "rw"},
        },
        working_dir=f"/autograder_jobs/{job_id}/submission"
    )

    return {
        "sandbox_id": job_id,
        "container_id": container.id,
        "working_dir": f"/autograder_jobs/{job_id}/submission"
    }

async def stop_sandbox(sandbox_id: str):
    """
    Stops the sandbox container and cleans up the directory.
    """
    client = get_docker_client()
    container_name = f"mentor-sandbox-{sandbox_id}"
    
    try:
        container = client.containers.get(container_name)
        container.stop(timeout=2)
        container.remove(force=True)
    except docker.errors.NotFound:
        pass
