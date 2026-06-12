import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.models import Assignment, Student, Submission, SubmissionOutbox, GradingJob, JobStatus, SubmissionSourceType, SubmissionStatus
from app.schemas.schemas import SubmissionCreateResponse
from app.services.storage_service import StorageService
from app.services.submission_validator import SubmissionValidator

logger = logging.getLogger(__name__)


class SubmissionService:
    @staticmethod
    async def submit_assignment(
        student: Student,
        assignment_id: uuid.UUID,
        source_type: SubmissionSourceType,
        repo_url: Optional[str],
        zip_bytes: Optional[bytes],
        db: AsyncSession,
    ) -> SubmissionCreateResponse:
        result = await db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.is_published == True,
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not published",
            )

        if source_type == SubmissionSourceType.ZIP and not zip_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP upload is required for zip source type",
            )
        if source_type == SubmissionSourceType.GITHUB and not repo_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="repo_url is required for GitHub submissions",
            )

        validator = SubmissionValidator()
        if source_type == SubmissionSourceType.ZIP:
            validator.validate_zip(zip_bytes, assignment.slug)
        else:
            await validator.validate_github(repo_url, assignment.slug)

        # Ensure active GradingSession exists
        from app.models.models import GradingSession, SessionStatus
        active_statuses = [
            SessionStatus.CREATED, SessionStatus.CHALLENGE_ISSUED,
            SessionStatus.RUNNING, SessionStatus.PROOF_GENERATED,
            SessionStatus.STARTED, SessionStatus.IN_PROGRESS
        ]
        session_query = await db.execute(
            select(GradingSession).where(
                GradingSession.student_id == student.id,
                GradingSession.assignment_id == assignment.id,
                GradingSession.status.in_(active_statuses),
            )
        )
        active_session = session_query.scalar_one_or_none()
        
        if not active_session:
            active_session = GradingSession(
                student_id=student.id,
                assignment_id=assignment.id,
                status=SessionStatus.CREATED,
            )
            db.add(active_session)
            await db.flush()

        submission = Submission(
            student_id=student.id,
            assignment_id=assignment.id,
            status=SubmissionStatus.QUEUED,
            source_type=source_type,
            repo_url=repo_url if source_type == SubmissionSourceType.GITHUB else None,
            submitted_at=datetime.utcnow(),
            attempt_number=await SubmissionService._resolve_attempt_number(student.id, assignment.id, db),
        )

        if source_type == SubmissionSourceType.ZIP:
            key = f"submissions/{assignment.slug}/{student.roll_number}/{uuid.uuid4().hex}.zip"
            storage_service = StorageService()
            await storage_service.upload_submission_zip(key, zip_bytes)
            submission.zip_object_key = key

        db.add(submission)
        import json
        payload = {
            "submission_id": str(submission.id),
            "student_id": str(student.id),
            "assignment_id": str(assignment.id),
            "assignment_slug": assignment.slug,
            "source_type": source_type.value,
            "repo_url": repo_url,
            "zip_object_key": submission.zip_object_key,
            "submitted_at": submission.submitted_at.isoformat(),
            "priority": 5, # default
        }

        # Create grading job record
        job = GradingJob(
            submission_id=submission.id,
            status=JobStatus.PENDING,
            queue_name="normal"
        )
        db.add(job)

        # Create outbox record
        outbox_msg = SubmissionOutbox(
            submission_id=submission.id,
            payload=json.dumps(payload),
        )
        db.add(outbox_msg)

        await db.commit()


        return SubmissionCreateResponse(
            submission_id=submission.id,
            assignment_id=submission.assignment_id,
            student_id=submission.student_id,
            status=submission.status,
            source_type=submission.source_type,
            repo_url=submission.repo_url,
            zip_object_key=submission.zip_object_key,
            submitted_at=submission.submitted_at,
            attempt_number=submission.attempt_number,
        )

    @staticmethod
    async def _resolve_attempt_number(student_id: uuid.UUID, assignment_id: uuid.UUID, db: AsyncSession) -> int:
        count_query = await db.execute(
            select(func.count()).select_from(Submission).where(
                Submission.student_id == student_id,
                Submission.assignment_id == assignment_id,
            )
        )
        previous_attempts = count_query.scalar_one()
        return max(1, (previous_attempts or 0) + 1)
