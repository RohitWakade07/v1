import re
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password
from app.core.config import settings
from app.core.rate_limit import check_rate_limit, client_ip
from app.db.session import get_db
from app.models.models import Student, Mentor, UserRole, Classroom, ClassroomEnrollment
from app.services.auth_service import AuthService
from app.api.v1.dependencies import get_current_student, get_current_mentor
from app.schemas.schemas import (
    StudentLoginRequest,
    MentorLoginRequest,
    TokenResponse,
    StudentCreate,
    StudentPublic,
    ErrorResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

PASSWORD_REGEX = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{8,}$')


def _raise_auth_error(result):
    """Convert an AuthResult with an error_code to a specific HTTPException."""
    code = result.error_code
    msg = result.error_message
    if code in ("USERNAME_NOT_FOUND",):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"error": code, "message": msg})
    if code in ("INVALID_PASSWORD", "WRONG_CURRENT_PASSWORD", "SAME_AS_OLD_PASSWORD", "WEAK_PASSWORD"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error": code, "message": msg})
    if code in ("ACCOUNT_INACTIVE", "ACCOUNT_LOCKED"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail={"error": code, "message": msg})
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"error": code, "message": msg})


@router.post(
    "/student/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def student_login(
    request: Request,
    body: StudentLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(
        client_ip(request),
        "student_login",
        limit=settings.LOGIN_RATE_LIMIT_PER_MINUTE,
    )

    result = await AuthService.login_student(body.roll_number, body.password, db)
    if not result.success:
        _raise_auth_error(result)
    return result.token


@router.post(
    "/mentor/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def mentor_login(
    request: Request,
    body: MentorLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(
        client_ip(request),
        "mentor_login",
        limit=settings.LOGIN_RATE_LIMIT_PER_MINUTE,
    )

    result = await AuthService.login_mentor(body.username, body.password, db)
    if not result.success:
        _raise_auth_error(result)
    return result.token


@router.post(
    "/student/register",
    response_model=StudentPublic,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def register_student(
    request: Request,
    body: StudentCreate,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(
        client_ip(request),
        "student_register",
        limit=settings.REGISTER_RATE_LIMIT_PER_MINUTE,
    )

    # Check roll number uniqueness
    existing_roll = await db.execute(
        select(Student).where(Student.roll_number == body.roll_number.upper())
    )
    if existing_roll.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "ROLL_NUMBER_EXISTS", "message": f"Roll number '{body.roll_number}' is already registered"},
        )

    # Check email uniqueness
    existing_email = await db.execute(
        select(Student).where(Student.email == body.email.lower())
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "EMAIL_EXISTS", "message": "An account with this email already exists"},
        )

    # Validate password strength
    if not PASSWORD_REGEX.match(body.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "WEAK_PASSWORD", "message": "Password must be at least 8 characters and include a number"},
        )

    classroom = None
    if body.class_code:
        code_clean = body.class_code.strip().upper()
        classroom_result = await db.execute(
            select(Classroom).where(Classroom.class_code == code_clean)
        )
        classroom = classroom_result.scalar_one_or_none()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "INVALID_CLASS_CODE", "message": "Invalid class code — please check with your mentor."},
            )

    student = Student(
        roll_number=body.roll_number.upper(),
        full_name=body.full_name,
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
    )
    db.add(student)
    await db.flush()

    if classroom:
        enrollment = ClassroomEnrollment(
            classroom_id=classroom.id,
            student_id=student.id,
            status="PENDING",
        )
        db.add(enrollment)
        await db.flush()

    await db.commit()
    await db.refresh(student)

    return StudentPublic(
        id=student.id,
        roll_number=student.roll_number,
        full_name=student.full_name,
        email=student.email,
        is_active=student.is_active,
        created_at=student.created_at,
    )


# ── Change Password ───────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post(
    "/student/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change student password",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def student_change_password(
    body: ChangePasswordRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await AuthService.change_student_password(
        current_student, body.current_password, body.new_password, db
    )
    if result.error_code:
        _raise_auth_error(result)
    return {"message": "Password updated successfully"}


@router.post(
    "/mentor/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change mentor/admin password",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def mentor_change_password(
    body: ChangePasswordRequest,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    result = await AuthService.change_mentor_password(
        current_mentor, body.current_password, body.new_password, db
    )
    if result.error_code:
        _raise_auth_error(result)
    return {"message": "Password updated successfully"}
