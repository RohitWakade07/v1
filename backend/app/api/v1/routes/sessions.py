import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Assignment, ClassroomEnrollment, Student
from app.api.v1.dependencies import get_current_student, get_approved_student
from app.services.session_service import SessionService
from app.schemas.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatusResponse,
    EvaluatorSessionCreateRequest,
    ErrorResponse,
    ChallengePackageResponse,
)
from app.core.config import settings

router = APIRouter(prefix="/sessions", tags=["Grading Sessions"])


@router.post(
    "",
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
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the grader binary when the student selects an assignment.
    Returns session_id which is embedded into the proof file.
    """
    return await SessionService.create_session(current_student.id, body, db)


@router.post(
    "/start-evaluator",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Create a session when the evaluator starts",
)
async def create_session_from_evaluator(
    body: EvaluatorSessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    x_evaluator_key: str | None = Header(default=None, alias="X-Evaluator-Key"),
):
    if not settings.EVALUATOR_SHARED_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evaluator shared key is not configured",
        )
    if not x_evaluator_key or x_evaluator_key != settings.EVALUATOR_SHARED_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid evaluator key",
        )

    roll = body.student_roll.strip().upper()
    result = await db.execute(
        select(Student).where(Student.roll_number == roll)
    )
    student = result.scalar_one_or_none()
    if not student or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or inactive",
        )

    enrollment_result = await db.execute(
        select(ClassroomEnrollment).where(
            ClassroomEnrollment.student_id == student.id,
            ClassroomEnrollment.status == "APPROVED",
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not approved in any classroom",
        )

    assignment_result = await db.execute(
        select(Assignment).where(
            Assignment.slug == body.assignment_slug,
            Assignment.is_published == True,
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not published",
        )

    return await SessionService.create_session(
        student.id,
        SessionCreateRequest(assignment_id=assignment.id),
        db,
        allow_existing=True,
    )


@router.patch(
    "/{session_id}/start",
    response_model=SessionStatusResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Mark session as in-progress (grader has started executing)",
)
async def mark_in_progress(
    session_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.mark_in_progress(
        uuid.UUID(session_id), current_student.id, db
    )


@router.post(
    "/{session_id}/payload",
    response_model=SessionStatusResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Submit the evaluator execution payload",
)
async def submit_session_payload(
    session_id: str,
    file: UploadFile = File(...),
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    payload_content = content.decode("utf-8", errors="replace")
    return await SessionService.save_payload(
        uuid.UUID(session_id), current_student.id, payload_content, db
    )


@router.post(
    "/{session_id}/abort",
    response_model=SessionStatusResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Abort a grading session",
)
async def abort_session(
    session_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.abort_session(
        uuid.UUID(session_id), current_student.id, db
    )


@router.get(
    "",
    response_model=list[SessionStatusResponse],
    summary="List all my sessions",
)
async def list_my_sessions(
    current_student: Student = Depends(get_approved_student),
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
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.get_status(
        uuid.UUID(session_id), current_student.id, db
    )


@router.get(
    "/{session_id}/challenge",
    response_model=ChallengePackageResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
    summary="Get the challenge package for local evaluation",
)
async def get_session_challenge(
    session_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.get_challenge_package(
        uuid.UUID(session_id), current_student, db
    )
