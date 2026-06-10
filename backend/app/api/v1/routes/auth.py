from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password
from app.core.config import settings
from app.db.session import get_db
from app.db.redis import get_redis, rate_limit_key
from app.models.models import Student, Mentor, UserRole, Classroom, ClassroomEnrollment
from app.services.auth_service import AuthService
from app.schemas.schemas import (
    StudentLoginRequest,
    MentorLoginRequest,
    TokenResponse,
    StudentCreate,
    StudentPublic,
    ErrorResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/student/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def student_login(
    request: Request,
    body: StudentLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    redis = await get_redis()
    ip = request.client.host
    key = rate_limit_key(ip, "student_login")
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > settings.LOGIN_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a minute.",
        )

    token = await AuthService.login_student(body.roll_number, body.password, db)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid roll number or password",
        )
    return token


@router.post(
    "/mentor/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def mentor_login(
    body: MentorLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    token = await AuthService.login_mentor(body.username, body.password, db)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return token


@router.post(
    "/student/register",
    response_model=StudentPublic,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
async def register_student(
    body: StudentCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Student).where(Student.roll_number == body.roll_number.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Roll number {body.roll_number} already registered",
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
                detail="Invalid class code — please check with your mentor.",
            )

    student = Student(
        roll_number=body.roll_number.upper(),
        full_name=body.full_name,
        email=body.email,
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

    return StudentPublic(
        id=student.id,
        roll_number=student.roll_number,
        full_name=student.full_name,
        email=student.email,
        is_active=student.is_active,
        created_at=student.created_at,
    )
