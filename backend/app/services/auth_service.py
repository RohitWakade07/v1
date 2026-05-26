from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from jose import JWTError

from app.models.models import Student, Mentor, UserRole
from app.core.security import verify_password, create_access_token, decode_access_token
from app.core.config import settings
from app.schemas.schemas import TokenResponse


class AuthService:

    @staticmethod
    async def login_student(
        roll_number: str,
        password: str,
        db: AsyncSession,
    ) -> Optional[TokenResponse]:
        result = await db.execute(
            select(Student).where(Student.roll_number == roll_number.upper())
        )
        student: Optional[Student] = result.scalar_one_or_none()

        if not student:
            return None
        if not student.is_active:
            return None
        if not verify_password(password, student.hashed_password):
            return None

        token = create_access_token(
            subject=student.roll_number,
            role=UserRole.STUDENT,
            extra_claims={"student_uuid": str(student.id)},
        )
        return TokenResponse(
            access_token=token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=UserRole.STUDENT,
            subject_id=student.roll_number,
        )

    @staticmethod
    async def login_mentor(
        username: str,
        password: str,
        db: AsyncSession,
    ) -> Optional[TokenResponse]:
        result = await db.execute(
            select(Mentor).where(Mentor.username == username)
        )
        mentor: Optional[Mentor] = result.scalar_one_or_none()

        if not mentor:
            return None
        if not mentor.is_active:
            return None
        if not verify_password(password, mentor.hashed_password):
            return None

        token = create_access_token(
            subject=mentor.username,
            role=mentor.role,
            extra_claims={"mentor_uuid": str(mentor.id)},
        )
        return TokenResponse(
            access_token=token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=mentor.role,
            subject_id=mentor.username,
        )

    @staticmethod
    def get_current_user_payload(token: str) -> dict:
        """Decode and return JWT payload. Raises JWTError if invalid."""
        return decode_access_token(token)
