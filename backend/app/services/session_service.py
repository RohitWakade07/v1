import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status

from app.models.models import GradingSession, Assignment, Student, SessionStatus, HeartbeatLog
from app.schemas.schemas import (
    SessionCreateResponse,
    SessionStatusResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    FinalizeRequest,
    FinalizeResponse,
)
from app.core.config import settings
from app.db.redis import get_redis, session_heartbeat_key, session_sequence_key


# Valid state transitions — enforced on every operation
VALID_TRANSITIONS: dict[SessionStatus, list[SessionStatus]] = {
    SessionStatus.CREATED: [SessionStatus.CHALLENGE_ISSUED, SessionStatus.TERMINATED],
    SessionStatus.CHALLENGE_ISSUED: [SessionStatus.EXECUTING, SessionStatus.TERMINATED, SessionStatus.EXPIRED],
    SessionStatus.EXECUTING: [SessionStatus.WAITING_HEARTBEAT, SessionStatus.TERMINATED, SessionStatus.EXPIRED],
    SessionStatus.WAITING_HEARTBEAT: [SessionStatus.EXECUTING, SessionStatus.FINALIZING, SessionStatus.TERMINATED, SessionStatus.EXPIRED],
    SessionStatus.FINALIZING: [SessionStatus.COMPLETED, SessionStatus.TERMINATED],
    SessionStatus.COMPLETED: [],
    SessionStatus.TERMINATED: [],
    SessionStatus.EXPIRED: [],
}


class SessionService:

    @staticmethod
    async def create_session(
        student_id: uuid.UUID,
        assignment_id: uuid.UUID,
        db: AsyncSession,
    ) -> SessionCreateResponse:
        # Verify assignment exists and is published
        assignment_result = await db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.is_published == True,
            )
        )
        assignment = assignment_result.scalar_one_or_none()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not published",
            )

        # Check deadline
        if assignment.deadline and datetime.now(timezone.utc) > assignment.deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed",
            )

        # Prevent duplicate active sessions for same student + assignment
        existing_result = await db.execute(
            select(GradingSession).where(
                GradingSession.student_id == student_id,
                GradingSession.assignment_id == assignment_id,
                GradingSession.status.in_([
                    SessionStatus.CREATED,
                    SessionStatus.CHALLENGE_ISSUED,
                    SessionStatus.EXECUTING,
                    SessionStatus.WAITING_HEARTBEAT,
                ]),
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Active session already exists: {existing.id}",
            )

        session = GradingSession(
            student_id=student_id,
            assignment_id=assignment_id,
            status=SessionStatus.CREATED,
        )
        db.add(session)
        await db.flush()  # get the id before commit

        # Set heartbeat TTL in Redis — if this key expires, session is EXPIRED
        redis = await get_redis()
        await redis.setex(
            session_heartbeat_key(str(session.id)),
            settings.SESSION_HEARTBEAT_TIMEOUT_SECONDS,
            "alive",
        )
        await redis.set(session_sequence_key(str(session.id)), 0)

        return SessionCreateResponse(
            session_id=session.id,
            status=session.status,
            created_at=session.created_at,
        )

    @staticmethod
    async def get_session_status(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> SessionStatusResponse:
        session = await SessionService._get_owned_session(session_id, student_id, db)
        return SessionStatusResponse(
            session_id=session.id,
            status=session.status,
            last_sequence=session.last_sequence,
            expected_sequence=session.expected_sequence,
            last_heartbeat_at=session.last_heartbeat_at,
            anomaly_detected=session.anomaly_detected,
        )

    @staticmethod
    async def process_heartbeat(
        request: HeartbeatRequest,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> HeartbeatResponse:
        session = await SessionService._get_owned_session(
            request.session_id, student_id, db
        )

        # Guard: session must be in an active state
        if session.status in [
            SessionStatus.COMPLETED,
            SessionStatus.TERMINATED,
            SessionStatus.EXPIRED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is {session.status} — cannot accept heartbeat",
            )

        # Nonce binding check
        if session.nonce and session.nonce != request.nonce:
            await SessionService._terminate_with_anomaly(
                session, db, "Nonce mismatch in heartbeat"
            )
            return HeartbeatResponse(
                decision="terminate",
                reason="Nonce mismatch",
                next_expected_sequence=0,
            )

        # Sequence enforcement — must arrive in strict order
        if request.sequence != session.expected_sequence:
            await SessionService._terminate_with_anomaly(
                session, db,
                f"Sequence mismatch: expected {session.expected_sequence}, got {request.sequence}",
            )
            return HeartbeatResponse(
                decision="terminate",
                reason="Sequence integrity violation",
                next_expected_sequence=0,
            )

        # Check Redis TTL — did the heartbeat arrive within the timeout window?
        redis = await get_redis()
        ttl_key = session_heartbeat_key(str(session.id))
        ttl = await redis.ttl(ttl_key)
        if ttl <= 0:
            # Key expired — mark session expired
            session.status = SessionStatus.EXPIRED
            db.add(session)
            return HeartbeatResponse(
                decision="terminate",
                reason="Heartbeat timeout exceeded",
                next_expected_sequence=0,
            )

        # All checks passed — accept heartbeat
        now = datetime.now(timezone.utc)
        session.last_heartbeat_at = now
        session.last_sequence = request.sequence
        session.expected_sequence = request.sequence + 1
        session.status = SessionStatus.EXECUTING

        # Reset heartbeat TTL window
        await redis.setex(
            ttl_key,
            settings.SESSION_HEARTBEAT_TIMEOUT_SECONDS,
            "alive",
        )
        await redis.set(session_sequence_key(str(session.id)), request.sequence)

        # Write immutable audit log
        log = HeartbeatLog(
            session_id=session.id,
            sequence=request.sequence,
            phase=request.phase,
            stdout_hash=request.stdout_hash,
            stderr_hash=request.stderr_hash,
            artifact_hashes=json.dumps(request.artifact_hashes or []),
            decision="continue",
        )
        db.add(log)
        db.add(session)

        return HeartbeatResponse(
            decision="continue",
            reason=None,
            next_expected_sequence=session.expected_sequence,
        )

    @staticmethod
    async def finalize_session(
        request: FinalizeRequest,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> FinalizeResponse:
        session = await SessionService._get_owned_session(
            request.session_id, student_id, db
        )

        if session.status not in [SessionStatus.EXECUTING, SessionStatus.WAITING_HEARTBEAT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot finalize session in status {session.status}",
            )

        # Sequence completeness check
        if request.final_sequence != session.last_sequence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Final sequence does not match last accepted sequence",
            )

        # Placeholder scoring — Phase 4 will implement full scoring engine
        final_score = await SessionService._compute_placeholder_score(session, db)

        session.status = SessionStatus.COMPLETED
        session.final_score = final_score
        session.completed_at = datetime.now(timezone.utc)
        db.add(session)

        # Clean up Redis keys
        redis = await get_redis()
        await redis.delete(session_heartbeat_key(str(session.id)))
        await redis.delete(session_sequence_key(str(session.id)))

        return FinalizeResponse(
            session_id=session.id,
            status=session.status,
            final_score=final_score,
            message="Session finalized successfully",
        )

    # ─── Internal helpers ───────────────────────────────────────────────────

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
    async def _terminate_with_anomaly(
        session: GradingSession,
        db: AsyncSession,
        reason: str,
    ) -> None:
        session.status = SessionStatus.TERMINATED
        session.anomaly_detected = True
        session.anomaly_notes = reason
        db.add(session)

    @staticmethod
    async def _compute_placeholder_score(
        session: GradingSession,
        db: AsyncSession,
    ) -> float:
        """
        Placeholder — Phase 4 scoring engine replaces this.
        Currently returns score proportional to heartbeats completed.
        """
        result = await db.execute(
            select(HeartbeatLog).where(HeartbeatLog.session_id == session.id)
        )
        logs = result.scalars().all()
        completed = len([l for l in logs if l.decision == "continue"])
        return min(100.0, completed * 10.0)
