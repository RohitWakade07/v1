import os
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class WorkspaceManager:
    def __init__(self, base_dir: str = "/tmp/autograder_jobs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, submission_id: int, code: str, language: str, assignment_id: int = 1) -> dict:
        """
        Creates a temporary workspace for a submission with submission/ and results/ folders.
        Returns a dictionary containing the host paths for volume mounting.
        """
        job_dir = self.base_dir / str(submission_id)
        
        # Ensure clean state if it previously existed
        if job_dir.exists():
            shutil.rmtree(job_dir)
            
        submission_dir = job_dir / "submission"
        results_dir = job_dir / "results"
        logs_dir = job_dir / "logs"
        
        submission_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        
        # Write student code
        extension = ".sh" if language == "bash" else ".py"
        main_file = submission_dir / f"main{extension}"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Copy instructor files if they exist for this assignment
        instructor_files_dir = Path(f"/home/werewolf/eep-software/autograder-system/instructor_files/week-{assignment_id:02d}")
        if instructor_files_dir.exists():
            for item in instructor_files_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, submission_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, submission_dir / item.name, dirs_exist_ok=True)
            logger.info(f"Copied instructor files from {instructor_files_dir} to {submission_dir}")
            
        logger.info(f"Workspace created for submission {submission_id} at {job_dir}")
        
        # Set permissions for the results directory so the non-root container user can write to it
        # 777 is used here because the container user 'grader' will have a different UID than the host
        os.chmod(results_dir, 0o777)
        
        return {
            "job_dir": str(job_dir),
            "submission_dir": str(submission_dir),
            "results_dir": str(results_dir),
            "logs_dir": str(logs_dir)
        }

    def cleanup_workspace(self, submission_id: int):
        """
        Removes the temporary workspace.
        """
        job_dir = self.base_dir / str(submission_id)
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up workspace for submission {submission_id}")
            except Exception as e:
                logger.error(f"Failed to clean up workspace {job_dir}: {str(e)}")
