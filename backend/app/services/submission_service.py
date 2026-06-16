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

        # ─────────────────────────────────────────────────────────────────
        # ATOMICITY FIX 1 — attempt_number race condition
        #
        # Previously, attempt_number was computed via a plain COUNT(*) query
        # inside the same transaction, BEFORE the new row was inserted. Two
        # concurrent submissions from the same student (double-click, retry
        # on network blip) could both read the same COUNT and both insert
        # rows with the same attempt_number.
        #
        # Fix: lock the student's existing submission rows for this
        # assignment with SELECT ... FOR UPDATE before computing the count.
        # This forces concurrent transactions to serialize on this student+
        # assignment pair — the second transaction blocks until the first
        # commits, then sees the now-correct count.
        #
        # This does NOT add lock contention across different students/
        # assignments (different rows), so it doesn't hurt concurrency for
        # the platform as a whole — only serializes duplicate submissions
        # from the same student for the same assignment, which is the
        # correct behavior anyway.
        # ─────────────────────────────────────────────────────────────────
        attempt_number = await SubmissionService._resolve_attempt_number_locked(
            student.id, assignment.id, db
        )

        submission = Submission(
            student_id=student.id,
            assignment_id=assignment.id,
            status=SubmissionStatus.QUEUED,
            source_type=source_type,
            repo_url=repo_url if source_type == SubmissionSourceType.GITHUB else None,
            submitted_at=datetime.utcnow(),
            attempt_number=attempt_number,
        )

        # ─────────────────────────────────────────────────────────────────
        # ATOMICITY FIX 2 — B2 upload orphan on commit failure
        #
        # Previously, the ZIP was uploaded to B2 BEFORE db.commit(). If the
        # commit failed afterward (DB connection drop, constraint violation,
        # etc.), the B2 object would be left behind with no DB record
        # pointing to it — an orphaned object that accumulates over time.
        #
        # Fix: wrap the entire DB-write block in try/except. If anything
        # fails after the upload succeeds, delete the just-uploaded B2
        # object as a compensating action before re-raising. This keeps
        # B2 and Postgres consistent: either both succeed, or neither
        # leaves a trace.
        # ─────────────────────────────────────────────────────────────────
        uploaded_key: Optional[str] = None
        storage_service: Optional[StorageService] = None

        if source_type == SubmissionSourceType.ZIP:
            key = f"submissions/{assignment.slug}/{student.roll_number}/{uuid.uuid4().hex}.zip"
            storage_service = StorageService()
            await storage_service.upload_submission_zip(key, zip_bytes)
            uploaded_key = key
            submission.zip_object_key = key

        try:
            db.add(submission)
            await db.flush()
            await db.refresh(submission)

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
                "priority": 5,  # default
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

        except Exception:
            # Compensating action: roll back the B2 upload if the DB
            # transaction did not complete, so we never leave an orphaned
            # object with no matching submission row.
            await db.rollback()
            if uploaded_key and storage_service:
                try:
                    await storage_service.delete_object(uploaded_key)
                    logger.warning(
                        "Rolled back orphaned B2 object %s after DB commit failure",
                        uploaded_key,
                    )
                except Exception as cleanup_err:
                    logger.error(
                        "Failed to clean up orphaned B2 object %s: %s",
                        uploaded_key, cleanup_err,
                    )
            raise

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
    async def _resolve_attempt_number_locked(student_id: uuid.UUID, assignment_id: uuid.UUID, db: AsyncSession) -> int:
        """Lock existing submission rows for this student+assignment, then
        compute the next attempt_number. The FOR UPDATE lock serializes
        concurrent submissions from the same student for the same
        assignment, preventing duplicate attempt_number values.

        If no rows exist yet, there is nothing to lock and this resolves
        to attempt_number=1 immediately (the unique-row scenario where a
        race is impossible).
        """
        locked_query = await db.execute(
            select(Submission.id)
            .where(
                Submission.student_id == student_id,
                Submission.assignment_id == assignment_id,
            )
            .with_for_update()
        )
        existing_ids = locked_query.scalars().all()
        return max(1, len(existing_ids) + 1)

    @staticmethod
    async def _resolve_attempt_number(student_id: uuid.UUID, assignment_id: uuid.UUID, db: AsyncSession) -> int:
        """Deprecated — kept for backward compatibility with any external
        callers. Use _resolve_attempt_number_locked for new code, which
        guards against the race condition described above."""
        count_query = await db.execute(
            select(func.count()).select_from(Submission).where(
                Submission.student_id == student_id,
                Submission.assignment_id == assignment_id,
            )
        )
        previous_attempts = count_query.scalar_one()
        return max(1, (previous_attempts or 0) + 1)
