import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import (
    Assignment,
    GradingSession,
    SessionStatus,
)
from app.schemas.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatusResponse,
)


ACTIVE_STATUSES = [SessionStatus.STARTED, SessionStatus.IN_PROGRESS]


class SessionService:

    @staticmethod
    async def create_session(
        student_id: uuid.UUID,
        request: SessionCreateRequest,
        db: AsyncSession,
    ) -> SessionCreateResponse:

        # 1. Assignment must exist and be published
        result = await db.execute(
            select(Assignment).where(
                Assignment.id == request.assignment_id,
                Assignment.is_published == True,
            )
        )
        assignment: Optional[Assignment] = result.scalar_one_or_none()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not yet published",
            )

        # 2. Deadline check
        if assignment.deadline and datetime.now(timezone.utc) > assignment.deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed",
            )

        # 3. No duplicate active session for same student + assignment
        existing = await db.execute(
            select(GradingSession).where(
                GradingSession.student_id == student_id,
                GradingSession.assignment_id == request.assignment_id,
                GradingSession.status.in_(ACTIVE_STATUSES),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active session for this assignment",
            )

        session = GradingSession(
            student_id=student_id,
            assignment_id=request.assignment_id,
            status=SessionStatus.STARTED,
        )
        db.add(session)
        await db.flush()

        return SessionCreateResponse(
            session_id=session.id,
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            status=session.status,
            started_at=session.started_at,
        )

    @staticmethod
    async def mark_in_progress(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> SessionStatusResponse:
        """
        Called by the grader binary immediately after launch
        to signal that local execution has begun.
        """
        session = await SessionService._get_owned_session(
            session_id, student_id, db
        )
        if session.status != SessionStatus.STARTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark in-progress from status {session.status}",
            )
        session.status = SessionStatus.IN_PROGRESS
        db.add(session)
        return SessionService._to_status_response(session)

    @staticmethod
    async def get_status(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> SessionStatusResponse:
        session = await SessionService._get_owned_session(
            session_id, student_id, db
        )
        return SessionService._to_status_response(session)

    @staticmethod
    async def get_my_sessions(
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> list[SessionStatusResponse]:
        result = await db.execute(
            select(GradingSession)
            .where(GradingSession.student_id == student_id)
            .order_by(GradingSession.started_at.desc())
        )
        sessions = result.scalars().all()
        return [SessionService._to_status_response(s) for s in sessions]

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    async def _get_owned_session(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> GradingSession:
        result = await db.execute(
            select(GradingSession).where(
                GradingSession.id == session_id,
                GradingSession.student_id == student_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return session

    @staticmethod
    def _to_status_response(session: GradingSession) -> SessionStatusResponse:
        return SessionStatusResponse(
            session_id=session.id,
            assignment_id=session.assignment_id,
            status=session.status,
            started_at=session.started_at,
            submitted_at=session.submitted_at,
            completed_at=session.completed_at,
            final_score=session.final_score,
            rejection_reason=session.rejection_reason,
        )
