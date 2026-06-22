import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # HTTPAuthorizationCredentials used in get_token_from_request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.models import Student, Mentor, UserRole

bearer_scheme = HTTPBearer(auto_error=False)

async def get_token_from_request(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token: str | None = None,
) -> str:
    if credentials:
        return credentials.credentials
    if token:
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_student(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> Student:
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("role") != UserRole.STUDENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    result = await db.execute(
        select(Student).where(Student.roll_number == payload.get("sub"))
    )
    student = result.scalar_one_or_none()
    if not student or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student account not found or inactive",
        )
    return student


async def get_current_mentor(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> Mentor:
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role = payload.get("role")
    if role not in [UserRole.MENTOR.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor access required",
        )
    result = await db.execute(
        select(Mentor).where(Mentor.username == payload.get("sub"))
    )
    mentor = result.scalar_one_or_none()
    if not mentor or not mentor.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mentor account not found or inactive",
        )
    return mentor


async def get_current_admin(
    mentor: Mentor = Depends(get_current_mentor),
) -> Mentor:
    if mentor.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return mentor


async def get_approved_student(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> Student:
    from app.models.models import ClassroomEnrollment
    result = await db.execute(
        select(ClassroomEnrollment).where(
            ClassroomEnrollment.student_id == student.id,
            ClassroomEnrollment.status == "APPROVED"
        )
    )
    enrollment = result.scalars().first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Classroom approval required. Your enrollment request is either pending or you have not joined a class."
        )
    return student
