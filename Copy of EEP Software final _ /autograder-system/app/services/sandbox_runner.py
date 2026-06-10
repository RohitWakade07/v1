import docker
from docker.errors import ImageNotFound, APIError
from requests.exceptions import ReadTimeout
import logging

logger = logging.getLogger(__name__)


class SandboxRunner:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.client = None

    def run_grading_container(
        self,
        submission_id: int,
        language: str,
        submission_dir: str,
        results_dir: str,
        timeout_seconds: int = 120
    ) -> dict:
        """
        Runs student code in a hardened Docker sandbox.
        """
        if not self.client:
            raise RuntimeError("Docker client is not initialized. Worker lacks docker socket access.")

        image_name = f"grading-{language}:latest"
        container = None
        logs = ""
        timed_out = False
        oom_killed = False
        crashed = False
        exit_code = None

        try:
            volumes = {
                submission_dir: {"bind": "/autograder/submission", "mode": "ro"},
                results_dir: {"bind": "/autograder/results", "mode": "rw"},
            }

            tmpfs_mounts = {
                "/tmp": "rw,noexec,nosuid,size=64m",
                "/run": "rw,noexec,nosuid,size=16m",
                "/home/grader": "rw,noexec,nosuid,size=64m,mode=1777",
            }

            logger.info(f"Starting hardened grading container for submission {submission_id}")

            container = self.client.containers.run(
                image=image_name,
                command="./run_autograder.sh",
                volumes=volumes,
                tmpfs=tmpfs_mounts,
                detach=True,
                network_mode="none",
                mem_limit="128m",
                nano_cpus=1000000000,
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                user="grader",
                read_only=True,
                working_dir="/autograder",
                auto_remove=False,
            )

            wait_result = container.wait(timeout=timeout_seconds)
            exit_code = wait_result.get("StatusCode", 1)

            container.reload()
            oom_killed = container.attrs.get("State", {}).get("OOMKilled", False)

            if exit_code != 0 and not oom_killed:
                crashed = True

        except ReadTimeout:
            logger.warning(f"Submission {submission_id} timed out after {timeout_seconds}s")
            timed_out = True
            crashed = False
            if container:
                try:
                    container.kill()
                except APIError as e:
                    logger.error(f"Failed to kill timed-out container {container.id}: {e}")

        except ImageNotFound:
            logger.error(f"Sandbox image {image_name} not found.")
            logs = f"Internal Configuration Error: Grading environment '{image_name}' is not available."
            crashed = True

        except APIError as e:
            logger.error(f"Docker API error for submission {submission_id}: {e}")
            logs = f"Internal Sandbox Error: {str(e)}"
            crashed = True

        except Exception as e:
            logger.exception(f"Unexpected error running sandbox for submission {submission_id}")
            logs = f"Unexpected Internal Error: {str(e)}"
            crashed = True

        finally:
            if container:
                try:
                    raw_logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
                    logs = raw_logs[:10000]
                    if len(raw_logs) > 10000:
                        logs += "\n...[TRUNCATED BY SYSTEM TO 10KB]"
                except Exception as e:
                    logger.error(f"Failed to fetch logs for container {container.id}: {e}")

                try:
                    # container.remove(force=True) # Temporarily disabled for user verification
                    pass
                except Exception as e:
                    logger.error(f"Failed to remove container {container.id}: {e}")

        return {
            "logs": logs,
            "timed_out": timed_out,
            "oom_killed": oom_killed,
            "crashed": crashed,
            "exit_code": exit_code,
        }
