from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import Student
from app.api.v1.dependencies import get_current_student
from app.services.session_service import SessionService
from app.schemas.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatusResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    FinalizeRequest,
    FinalizeResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/session", tags=["Grading Session"])


@router.post(
    "/create",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def create_session(
    body: SessionCreateRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new grading session for the authenticated student.
    One active session per student per assignment is enforced.
    """
    return await SessionService.create_session(
        student_id=current_student.id,
        assignment_id=body.assignment_id,
        db=db,
    )


@router.get(
    "/{session_id}/status",
    response_model=SessionStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_session_status(
    session_id: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    return await SessionService.get_session_status(
        session_id=uuid.UUID(session_id),
        student_id=current_student.id,
        db=db,
    )


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def submit_heartbeat(
    body: HeartbeatRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Core supervision endpoint.
    Validates sequence, nonce binding, and TTL.
    Returns continue or terminate decision.
    """
    return await SessionService.process_heartbeat(
        request=body,
        student_id=current_student.id,
        db=db,
    )


@router.post(
    "/finalize",
    response_model=FinalizeResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def finalize_session(
    body: FinalizeRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete the session. Backend computes authoritative score.
    Student cannot modify or replay after this point.
    """
    return await SessionService.finalize_session(
        request=body,
        student_id=current_student.id,
        db=db,
    )
