import asyncio
import logging
from celery import Task
from app.celery_app import celery_app
from workers.docker_executor import DockerExecutor
from app.db.session import AsyncSessionLocal
from app.models.models import (
    Submission, SubmissionStatus, GradingJob, JobStatus,
    SubmissionResult, ExecutionMetrics, ExecutionLogs
)
from sqlalchemy import select
from datetime import datetime

logger = logging.getLogger(__name__)

class GradingTask(Task):
    abstract = True

@celery_app.task(
    base=GradingTask,
    bind=True,
    name="workers.tasks.grade_submission_task",
    max_retries=3,
    acks_late=True,
)
def grade_submission_task(self, submission_id: str):
    """Synchronous celery task wrapper that runs the async grading process."""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(async_grade_submission(submission_id, self.request.id))
    except Exception as e:
        logger.error(f"Task failed completely: {e}")
        raise self.retry(exc=e)

async def async_grade_submission(submission_id: str, celery_task_id: str):
    logger.info(f"Starting grading for submission {submission_id}")
    
    async with AsyncSessionLocal() as db:
        # Fetch job
        result = await db.execute(select(GradingJob).where(GradingJob.submission_id == submission_id))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"GradingJob not found for {submission_id}")
            return
            
        from app.models.models import Assignment
        sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
        submission = sub_result.scalar_one_or_none()
        
        if not submission:
            logger.error(f"Submission not found for {submission_id}")
            return
            
        assn_result = await db.execute(select(Assignment).where(Assignment.id == submission.assignment_id))
        assignment = assn_result.scalar_one_or_none()
        
        # Mark as processing
        job.status = JobStatus.PROCESSING
        job.celery_task_id = celery_task_id
        job.started_at = datetime.utcnow()
        submission.status = SubmissionStatus.RUNNING
        await db.commit()
        
        from app.db.redis import get_redis
        redis_client = await get_redis()
        lock_key = f"grading:lock:{submission_id}"
        
        # Try to acquire lock
        lock_acquired = await redis_client.set(lock_key, celery_task_id, nx=True, ex=300)
        if not lock_acquired:
            logger.warning(f"Submission {submission_id} is already being graded by another worker.")
            return

        try:
            executor = DockerExecutor()
            status_str, grading_result, exec_meta = await executor.execute(
                submission_id=str(submission.id),
                assignment_slug=assignment.slug,
                source_type=submission.source_type.value,
                repo_url=submission.repo_url,
                zip_object_key=submission.zip_object_key,
            )
        finally:
            await redis_client.delete(lock_key)
        
        # Save results atomically
        try:
            job.status = JobStatus.DONE if status_str == "COMPLETED" else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            
            submission.status = SubmissionStatus.COMPLETED if status_str == "COMPLETED" else SubmissionStatus.FAILED
            submission.score = grading_result.score
            submission.max_score = grading_result.max_score
            submission.passed = grading_result.passed
            submission.completed_at = datetime.utcnow()
            
            import json
            checks_json = json.dumps([c.model_dump() for c in grading_result.checks])
            
            sub_res = SubmissionResult(
                submission_id=submission.id,
                checks_json=checks_json,
                feedback=grading_result.feedback,
                stdout=exec_meta["stdout"],
                stderr=exec_meta["stderr"],
                execution_command=exec_meta["execution_command"],
                exit_code=exec_meta["exit_code"],
                execution_time_ms=exec_meta["execution_time_ms"],
                timed_out=exec_meta["timed_out"],
                oom_killed=exec_meta["oom_killed"],
                container_id=exec_meta["container_id"],
                grader_logs=exec_meta["grader_logs"]
            )
            db.add(sub_res)
            
            metrics = ExecutionMetrics(
                submission_id=submission.id,
                container_id=exec_meta["container_id"],
                wall_time_ms=exec_meta["execution_time_ms"]
            )
            db.add(metrics)
            
            logs = ExecutionLogs(
                submission_id=submission.id,
                log_level="INFO",
                message="Grading completed successfully" if status_str == "COMPLETED" else "Grading failed"
            )
            db.add(logs)
            
            await db.commit()
            logger.info(f"Grading complete for {submission_id}")
            
        except Exception as e:
            logger.error(f"Failed to save results for {submission_id}: {e}")
            await db.rollback()
            raise
