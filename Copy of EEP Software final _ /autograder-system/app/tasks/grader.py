import logging
from celery import Celery
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Submission
from app.services.workspace_manager import WorkspaceManager
from app.services.sandbox_runner import SandboxRunner
from app.services.result_parser import ResultParser

logger = logging.getLogger(__name__)

celery_app = Celery(
    "grader",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

workspace_manager = WorkspaceManager()
sandbox_runner = SandboxRunner()
result_parser = ResultParser()


@celery_app.task(name="grade_submission")
def grade_submission(submission_id: int):
    logger.info(f"Starting grading process for submission_id: {submission_id}")
    db = SessionLocal()
    workspace = None

    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found in database.")
            return

        submission.status = "running"
        db.commit()

        try:
            workspace = workspace_manager.create_workspace(submission.id, submission.code, submission.language, submission.assignment_id)
        except Exception as e:
            logger.exception(f"Failed to create workspace for submission {submission_id}: {e}")
            submission.status = "failed"
            submission.score = 0
            submission.feedback = "Internal Error: Could not prepare evaluation workspace."
            db.commit()
            return

        sandbox_result = sandbox_runner.run_grading_container(
            submission_id=submission.id,
            language=submission.language,
            submission_dir=workspace["submission_dir"],
            results_dir=workspace["results_dir"],
            timeout_seconds=10
        )

        submission.logs = sandbox_result["logs"]

        if sandbox_result["crashed"]:
            submission.status = "failed"
            submission.score = 0
            submission.feedback = "Internal Error: Sandbox failed to run properly."
        elif sandbox_result["oom_killed"]:
            submission.status = "failed"
            submission.score = 0
            submission.feedback = "Memory Limit Exceeded: Your code used more than the allowed 128MB."
        elif sandbox_result["timed_out"]:
            submission.status = "failed"
            submission.score = 0
            submission.feedback = "Execution Timeout: Your code took too long to execute or exhausted CPU resources."
        else:
            results = result_parser.parse(workspace["results_dir"])
            submission.status = results["status"]
            submission.score = results["score"]
            submission.feedback = results["feedback"]
            submission.execution_time_ms = results.get("execution_time_ms")

        db.commit()
        logger.info(f"Finished grading submission {submission_id}. Status: {submission.status}")

    except Exception as e:
        logger.exception(f"Unexpected error grading submission {submission_id}: {e}")
        db.rollback()
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                submission.status = "failed"
                submission.score = 0
                submission.feedback = "Internal Error: An unexpected exception occurred during evaluation."
                db.commit()
        except Exception:
            logger.exception(f"Failed to persist failure state for submission {submission_id}")

    finally:
        db.close()
        workspace_manager.cleanup_workspace(submission_id)
