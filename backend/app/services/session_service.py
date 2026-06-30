import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.cache import (
    TTL_SESSION,
    get_or_set,
    invalidate as cache_invalidate,
    session_cache_key,
)
from app.models.models import (
    Assignment,
    GradingSession,
    SessionStatus,
    AssignmentConfig,
    AssignmentGraderMapping,
    Student,
)
from app.schemas.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatusResponse,
    ChallengePackageResponse,
    ChallengeSessionMetadata,
    ChallengeAssignmentMetadata,
    ChallengeGraderMetadata,
)


ACTIVE_STATUSES = [
    SessionStatus.CREATED,
    SessionStatus.CHALLENGE_ISSUED,
    SessionStatus.RUNNING,
    SessionStatus.PROOF_GENERATED,
    SessionStatus.STARTED,
    SessionStatus.IN_PROGRESS,
]


class SessionService:

    @staticmethod
    async def create_session(
        student_id: uuid.UUID,
        request: SessionCreateRequest,
        db: AsyncSession,
        allow_existing: bool = False,
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
        if assignment.deadline and datetime.utcnow() > assignment.deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed",
            )

        # 3. No duplicate active session for same student + assignment
        existing_result = await db.execute(
            select(GradingSession).where(
                GradingSession.student_id == student_id,
                GradingSession.assignment_id == request.assignment_id,
                GradingSession.status.in_(ACTIVE_STATUSES),
            )
        )
        existing_session = existing_result.scalar_one_or_none()
        if existing_session:
            if allow_existing:
                return SessionService._to_create_response(existing_session, assignment)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active session for this assignment",
            )

        session = GradingSession(
            student_id=student_id,
            assignment_id=request.assignment_id,
            status=SessionStatus.CREATED,
        )
        db.add(session)
        await db.flush()

        return SessionService._to_create_response(session, assignment)

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
        if session.status not in (SessionStatus.CREATED, SessionStatus.CHALLENGE_ISSUED, SessionStatus.STARTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark in-progress from status {session.status}",
            )
        session.status = SessionStatus.RUNNING
        db.add(session)
        await db.flush()
        await cache_invalidate(session_cache_key(session_id, student_id))
        return SessionService._to_status_response(session)

    @staticmethod
    async def save_payload(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        payload_content: str,
        db: AsyncSession,
    ) -> SessionStatusResponse:
        session = await SessionService._get_owned_session(
            session_id, student_id, db
        )
        # Allow payload upload if session is CREATED, STARTED, RUNNING, CHALLENGE_ISSUED, or IN_PROGRESS
        if session.status not in (
            SessionStatus.CREATED,
            SessionStatus.STARTED,
            SessionStatus.RUNNING,
            SessionStatus.CHALLENGE_ISSUED,
            SessionStatus.IN_PROGRESS,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot upload payload to session in status {session.status}",
            )
        session.pending_payload = payload_content
        session.status = SessionStatus.PROOF_GENERATED
        db.add(session)
        await db.flush()
        await cache_invalidate(session_cache_key(session_id, student_id))
        return SessionService._to_status_response(session)

    @staticmethod
    def _to_create_response(
        session: GradingSession,
        assignment: Assignment,
    ) -> SessionCreateResponse:
        return SessionCreateResponse(
            session_id=session.id,
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            status=session.status,
            started_at=session.started_at,
        )

    @staticmethod
    async def get_status(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> SessionStatusResponse:
        async def _fetch() -> dict:
            session = await SessionService._get_owned_session(session_id, student_id, db)
            return SessionService._to_status_response(session).model_dump(mode="json")

        data = await get_or_set(session_cache_key(session_id, student_id), _fetch, TTL_SESSION)
        return SessionStatusResponse(**data)

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

    @staticmethod
    async def abort_session(
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        db: AsyncSession,
    ) -> SessionStatusResponse:
        session = await SessionService._get_owned_session(
            session_id, student_id, db
        )
        if session.status in [
            SessionStatus.VERIFIED,
            SessionStatus.FAILED,
            SessionStatus.ABORTED,
            SessionStatus.COMPLETED,
            SessionStatus.REJECTED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot abort session in terminal state {session.status}",
            )
        session.status = SessionStatus.ABORTED
        db.add(session)
        await db.flush()
        await cache_invalidate(session_cache_key(session_id, student_id))
        return SessionService._to_status_response(session)

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

    @staticmethod
    async def get_challenge_package(
        session_id: uuid.UUID,
        student: Student,
        db: AsyncSession,
    ) -> ChallengePackageResponse:
        # 1. Fetch GradingSession and ensure ownership
        session = await SessionService._get_owned_session(session_id, student.id, db)

        if session.status in (SessionStatus.CREATED, SessionStatus.STARTED):
            session.status = SessionStatus.CHALLENGE_ISSUED
            db.add(session)
            await db.flush()
            await cache_invalidate(session_cache_key(session_id, student.id))

        # 2. Fetch Assignment
        result = await db.execute(
            select(Assignment).where(Assignment.id == session.assignment_id)
        )
        assignment: Optional[Assignment] = result.scalar_one_or_none()
        if not assignment or not assignment.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not published",
            )

        # 3. Generate nonce if not already present
        if not session.proof_nonce:
            session.proof_nonce = str(uuid.uuid4())
            db.add(session)
            await db.flush()
            await cache_invalidate(session_cache_key(session_id, student.id))

        # 4. Fetch AssignmentConfig
        config_result = await db.execute(
            select(AssignmentConfig).where(AssignmentConfig.assignment_id == assignment.id)
        )
        config: Optional[AssignmentConfig] = config_result.scalar_one_or_none()
        rules = []
        constraints = {"timeout_seconds": 300}
        if config and config.config_data:
            try:
                import json
                parsed_config = json.loads(config.config_data)
                rules = parsed_config.get("validation_rules", [])
                constraints = parsed_config.get("execution_constraints", {"timeout_seconds": 300})
            except Exception:
                pass

        # 5. Fetch AssignmentGraderMapping to get Grader and GraderVersion
        mapping_result = await db.execute(
            select(AssignmentGraderMapping).where(
                AssignmentGraderMapping.assignment_id == assignment.id
            )
        )
        mapping: Optional[AssignmentGraderMapping] = mapping_result.scalar_one_or_none()
        
        grader_id = uuid.uuid4()
        grader_name = "Default Artifact Grader"
        grader_ver = "1.0.0"
        grader_hash = "a" * 64

        if mapping:
            from app.models.models import Grader, GraderVersion
            grader_res = await db.execute(
                select(Grader).where(Grader.id == mapping.grader_id)
            )
            grader: Optional[Grader] = grader_res.scalar_one_or_none()
            if grader:
                grader_id = grader.id
                grader_name = grader.name
            
            if mapping.grader_version_id:
                version_res = await db.execute(
                    select(GraderVersion).where(GraderVersion.id == mapping.grader_version_id)
                )
                version: Optional[GraderVersion] = version_res.scalar_one_or_none()
                if version:
                    grader_ver = version.version
                    grader_hash = version.binary_hash

        # 6. Return response
        return ChallengePackageResponse(
            session=ChallengeSessionMetadata(
                session_id=session.id,
                student_id=student.roll_number,
                nonce=session.proof_nonce,
                started_at=session.started_at,
            ),
            assignment=ChallengeAssignmentMetadata(
                assignment_id=assignment.id,
                slug=assignment.slug,
                title=assignment.title,
                category=assignment.category,
                max_score=assignment.max_score,
                deadline=assignment.deadline,
            ),
            grader=ChallengeGraderMetadata(
                grader_id=grader_id,
                name=grader_name,
                version=grader_ver,
                binary_hash=grader_hash,
            ),
            execution_constraints=constraints,
            validation_rules=rules,
        )
