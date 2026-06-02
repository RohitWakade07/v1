import uuid

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
    ErrorResponse,
)

router = APIRouter(prefix="/sessions", tags=["Grading Sessions"])


@router.post(
    "/",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
    summary="Open a grading session for the selected assignment",
)
async def create_session(
    body: SessionCreateRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the grader binary when the student selects an assignment.
    Returns session_id which is embedded into the proof file.
    """
    return await SessionService.create_session(current_student.id, body, db)


@router.patch(
    "/{session_id}/start",
    response_model=SessionStatusResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Mark session as in-progress (grader has started executing)",
)
async def mark_in_progress(
    session_id: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.mark_in_progress(
        uuid.UUID(session_id), current_student.id, db
    )


@router.get(
    "/",
    response_model=list[SessionStatusResponse],
    summary="List all my sessions",
)
async def list_my_sessions(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.get_my_sessions(current_student.id, db)


@router.get(
    "/{session_id}",
    response_model=SessionStatusResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get status of a specific session",
)
async def get_session(
    session_id: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.get_status(
        uuid.UUID(session_id), current_student.id, db
    )
