import asyncio
import json
import logging
import signal
import sys
import uuid
from datetime import datetime

from confluent_kafka import Consumer, KafkaError

from app.core.config import settings
from app.db.sync_session import SyncSessionLocal
from app.kafka import producer as kafka_producer
from app.models.models import Submission, SubmissionResult, SubmissionStatus
from workers.docker_executor import DockerExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUBMISSION_STATUS_EVENTS_TOPIC = "submission-status-events"
GRADING_RESULTS_TOPIC = "grading-results"

running = True


def signal_handler(sig, frame):
    global running
    logger.info("Termination signal received. Shutting down worker...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def publish_status_update(submission_id: str, student_id: str, status: str):
    payload = {
        "submission_id": submission_id,
        "student_id": student_id,
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "worker_id": "worker-1",
    }
    kafka_producer.publish(SUBMISSION_STATUS_EVENTS_TOPIC, key=submission_id, payload=payload)


def publish_grading_result(
    submission_id: str,
    student_id: str,
    assignment_id: str,
    score: float,
    max_score: float,
    passed: bool,
    checks: list,
    feedback: str,
    execution_time_ms: int,
):
    payload = {
        "submission_id": submission_id,
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": score,
        "max_score": max_score,
        "passed": passed,
        "checks": checks,
        "feedback": feedback,
        "execution_time_ms": execution_time_ms,
        "completed_at": datetime.utcnow().isoformat(),
    }
    kafka_producer.publish(GRADING_RESULTS_TOPIC, key=submission_id, payload=payload)


def process_message(msg_val: bytes):
    try:
        data = json.loads(msg_val.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse Kafka message JSON: {e}")
        return

    submission_id = data.get("submission_id")
    student_id = data.get("student_id")
    assignment_id = data.get("assignment_id")
    assignment_slug = data.get("assignment_slug")
    source_type = data.get("source_type")
    repo_url = data.get("repo_url")
    zip_object_key = data.get("zip_object_key")

    if not submission_id or not assignment_slug:
        logger.error("Missing critical fields in message.")
        return

    logger.info(f"Processing grading job for submission {submission_id} (slug: {assignment_slug})")

    # Update state to RUNNING
    with SyncSessionLocal() as session:
        sub = session.get(Submission, uuid.UUID(submission_id))
        if not sub:
            logger.error(f"Submission {submission_id} not found in database.")
            return
        sub.status = SubmissionStatus.RUNNING
        sub.started_at = datetime.utcnow()
        session.add(sub)
        session.commit()

    publish_status_update(submission_id, student_id, "RUNNING")

    # Instantiate executor
    executor = DockerExecutor()

    # Run execution lifecycle (async block run synchronously in loop)
    status_str, grading_res, exec_meta = asyncio.run(
        executor.execute(
            submission_id=submission_id,
            assignment_slug=assignment_slug,
            source_type=source_type,
            repo_url=repo_url,
            zip_object_key=zip_object_key,
        )
    )

    logger.info(f"Grading complete for {submission_id}. Status: {status_str}, Score: {grading_res.score}/{grading_res.max_score}")

    # Write results to DB using sync session
    with SyncSessionLocal() as session:
        sub = session.get(Submission, uuid.UUID(submission_id))
        if sub:
            sub.status = SubmissionStatus(status_str)
            sub.score = grading_res.score
            sub.max_score = grading_res.max_score
            sub.passed = grading_res.passed
            sub.completed_at = datetime.utcnow()
            session.add(sub)

            # Save check results as JSON
            checks_list = [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "marks": c.marks,
                    "max_marks": c.max_marks,
                    "reason": c.reason,
                    "hint": c.hint,
                }
                for c in grading_res.checks
            ]

            # Upsert SubmissionResult
            result_record = session.query(SubmissionResult).filter_by(submission_id=sub.id).first()
            if not result_record:
                result_record = SubmissionResult(
                    submission_id=sub.id,
                    created_at=datetime.utcnow()
                )

            result_record.checks_json = json.dumps(checks_list)
            result_record.feedback = grading_res.feedback
            result_record.stdout = exec_meta.get("stdout")
            result_record.stderr = exec_meta.get("stderr")
            result_record.execution_command = exec_meta.get("execution_command")
            result_record.exit_code = exec_meta.get("exit_code")
            result_record.execution_time_ms = exec_meta.get("execution_time_ms")
            result_record.timed_out = exec_meta.get("timed_out", False)
            result_record.oom_killed = exec_meta.get("oom_killed", False)
            result_record.container_id = exec_meta.get("container_id")
            result_record.grader_logs = exec_meta.get("grader_logs")
            result_record.ai_feedback = ""

            session.add(result_record)
            session.commit()

            # Publish status and results
            publish_status_update(submission_id, student_id, status_str)
            publish_grading_result(
                submission_id=submission_id,
                student_id=student_id,
                assignment_id=assignment_id,
                score=grading_res.score,
                max_score=grading_res.max_score,
                passed=grading_res.passed,
                checks=checks_list,
                feedback=grading_res.feedback,
                execution_time_ms=exec_meta.get("execution_time_ms", 0),
            )


def main():
    logger.info("Starting EYSIP Autograder Worker process...")
    conf = {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "grading-workers-group",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }

    consumer = Consumer(conf)
    consumer.subscribe(["grading-jobs"])

    while running:
        msg = consumer.poll(1.0)
        if msg is None:
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                logger.info(f"Reached end of partition: {msg.topic()} [{msg.partition()}]")
            else:
                logger.error(f"Kafka consumer error: {msg.error()}")
            continue

        # Process job
        process_message(msg.value())

    consumer.close()
    logger.info("Worker process shutdown complete.")


if __name__ == "__main__":
    main()
