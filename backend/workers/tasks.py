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
    """Synchronous Celery task wrapper that runs the async grading process."""
    logger.info(f"[TASK:RECEIVED] submission_id={submission_id} celery_task_id={self.request.id} retries={self.request.retries}")

    try:
        logger.info(f"[TASK:START] Running async grading coroutine for submission_id={submission_id}")
        result = asyncio.run(async_grade_submission(submission_id, self.request.id))
        logger.info(f"[TASK:DONE] submission_id={submission_id} result={result}")
        return result
    except Exception as e:
        logger.error(f"[TASK:FAILED] submission_id={submission_id} error={type(e).__name__}: {e}", exc_info=True)
        logger.info(f"[TASK:RETRY] Scheduling retry for submission_id={submission_id} attempt={self.request.retries + 1}/3")
        raise self.retry(exc=e, countdown=5 * (self.request.retries + 1))


async def async_grade_submission(submission_id: str, celery_task_id: str):
    logger.info(f"[GRADE:INIT] submission_id={submission_id} celery_task_id={celery_task_id}")

    async with AsyncSessionLocal() as db:

        # ── 1. Fetch GradingJob ────────────────────────────────────────────
        logger.debug(f"[GRADE:DB] Fetching GradingJob for submission_id={submission_id}")
        result = await db.execute(select(GradingJob).where(GradingJob.submission_id == submission_id))
        job = result.scalar_one_or_none()

        if not job:
            logger.error(f"[GRADE:DB] GradingJob NOT FOUND for submission_id={submission_id} — aborting task")
            return {"status": "aborted", "reason": "no_grading_job"}

        logger.info(f"[GRADE:DB] GradingJob found: id={job.id} status={job.status} attempt_count={job.attempt_count}")

        # ── 2. Fetch Submission ────────────────────────────────────────────
        logger.debug(f"[GRADE:DB] Fetching Submission id={submission_id}")
        sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
        submission = sub_result.scalar_one_or_none()

        if not submission:
            logger.error(f"[GRADE:DB] Submission NOT FOUND id={submission_id} — aborting task")
            return {"status": "aborted", "reason": "no_submission"}

        logger.info(f"[GRADE:DB] Submission found: student_id={submission.student_id} assignment_id={submission.assignment_id} source_type={submission.source_type} status={submission.status}")

        # ── 3. Fetch Assignment ────────────────────────────────────────────
        from app.models.models import Assignment
        logger.debug(f"[GRADE:DB] Fetching Assignment id={submission.assignment_id}")
        assn_result = await db.execute(select(Assignment).where(Assignment.id == submission.assignment_id))
        assignment = assn_result.scalar_one_or_none()

        if not assignment:
            logger.error(f"[GRADE:DB] Assignment NOT FOUND id={submission.assignment_id} — aborting task")
            return {"status": "aborted", "reason": "no_assignment"}

        logger.info(f"[GRADE:DB] Assignment found: slug={assignment.slug} title={assignment.title}")

        # ── 4. Mark as PROCESSING ──────────────────────────────────────────
        logger.info(f"[GRADE:STATUS] Marking job as PROCESSING and submission as RUNNING")
        job.status = JobStatus.PROCESSING
        job.celery_task_id = celery_task_id
        job.started_at = datetime.utcnow()
        job.attempt_count += 1
        submission.status = SubmissionStatus.RUNNING
        submission.started_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[GRADE:STATUS] DB commit OK — job.attempt_count={job.attempt_count}")

        # ── 5. Acquire distributed lock ────────────────────────────────────
        from app.db.redis import get_redis
        redis_client = await get_redis()
        lock_key = f"grading:lock:{submission_id}"

        logger.info(f"[GRADE:LOCK] Attempting to acquire lock key={lock_key}")
        lock_acquired = await redis_client.set(lock_key, celery_task_id, nx=True, ex=300)

        if not lock_acquired:
            existing_holder = await redis_client.get(lock_key)
            logger.warning(f"[GRADE:LOCK] Lock NOT acquired — already held by task_id={existing_holder} — skipping duplicate")
            return {"status": "skipped", "reason": "duplicate_lock"}

        logger.info(f"[GRADE:LOCK] Lock acquired successfully key={lock_key} ttl=300s")

        # ── 6. Execute grading ─────────────────────────────────────────────
        try:
            logger.info(f"[GRADE:EXEC] Starting DockerExecutor for submission_id={submission_id} slug={assignment.slug} source_type={submission.source_type.value}")
            executor = DockerExecutor()
            status_str, grading_result, exec_meta = await executor.execute(
                submission_id=str(submission.id),
                assignment_slug=assignment.slug,
                source_type=submission.source_type.value,
                repo_url=submission.repo_url,
                zip_object_key=submission.zip_object_key,
            )
            logger.info(
                f"[GRADE:EXEC] Execution finished: status={status_str} "
                f"score={grading_result.score}/{grading_result.max_score} "
                f"passed={grading_result.passed} "
                f"exit_code={exec_meta['exit_code']} "
                f"timed_out={exec_meta['timed_out']} "
                f"oom_killed={exec_meta['oom_killed']} "
                f"execution_time_ms={exec_meta['execution_time_ms']} "
                f"container_id={exec_meta['container_id'][:12] if exec_meta['container_id'] else 'none'}"
            )
            logger.debug(f"[GRADE:EXEC] stdout preview: {exec_meta['stdout'][:500]!r}")
            logger.debug(f"[GRADE:EXEC] checks count: {len(grading_result.checks)}")
            for i, check in enumerate(grading_result.checks):
                logger.debug(f"[GRADE:EXEC] check[{i}] name={check.name} passed={check.passed} marks={check.marks}/{check.max_marks}")

        finally:
            logger.info(f"[GRADE:LOCK] Releasing lock key={lock_key}")
            await redis_client.delete(lock_key)
            logger.info(f"[GRADE:LOCK] Lock released")

        # ── 7. Save results atomically ─────────────────────────────────────
        logger.info(f"[GRADE:SAVE] Saving results to DB for submission_id={submission_id}")
        try:
            import json

            job.status = JobStatus.DONE if status_str == "COMPLETED" else JobStatus.FAILED
            job.completed_at = datetime.utcnow()

            submission.status = SubmissionStatus.COMPLETED if status_str == "COMPLETED" else SubmissionStatus.FAILED
            submission.score = grading_result.score
            submission.max_score = grading_result.max_score
            submission.passed = grading_result.passed
            submission.completed_at = datetime.utcnow()

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
                grader_logs=exec_meta["grader_logs"],
            )
            db.add(sub_res)
            logger.debug(f"[GRADE:SAVE] SubmissionResult row added")

            metrics = ExecutionMetrics(
                submission_id=submission.id,
                container_id=exec_meta["container_id"],
                wall_time_ms=exec_meta["execution_time_ms"],
            )
            db.add(metrics)
            logger.debug(f"[GRADE:SAVE] ExecutionMetrics row added")

            logs = ExecutionLogs(
                submission_id=submission.id,
                log_level="INFO",
                message="Grading completed successfully" if status_str == "COMPLETED" else "Grading failed",
            )
            db.add(logs)
            logger.debug(f"[GRADE:SAVE] ExecutionLogs row added")

            await db.commit()
            logger.info(
                f"[GRADE:SAVE] DB commit OK — "
                f"submission_id={submission_id} "
                f"final_status={submission.status} "
                f"score={submission.score}/{submission.max_score} "
                f"passed={submission.passed}"
            )

        except Exception as e:
            logger.error(f"[GRADE:SAVE] FAILED to save results for submission_id={submission_id}: {type(e).__name__}: {e}", exc_info=True)
            await db.rollback()
            logger.error(f"[GRADE:SAVE] DB rolled back")
            raise

    logger.info(f"[GRADE:COMPLETE] submission_id={submission_id} fully processed")
    return {
        "status": status_str,
        "score": grading_result.score,
        "max_score": grading_result.max_score,
        "passed": grading_result.passed,
    }
