"""Auth service with structured error returns for specific error codes."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.security import verify_password, create_access_token, hash_password
from app.models.models import Student, Mentor, UserRole
from app.schemas.schemas import TokenResponse


@dataclass
class AuthResult:
    token: Optional[TokenResponse] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.token is not None


class AuthService:

    @staticmethod
    async def login_student(
        roll_number: str,
        password: str,
        db: AsyncSession,
    ) -> AuthResult:
        result = await db.execute(
            select(Student).where(Student.roll_number == roll_number.upper())
        )
        student: Optional[Student] = result.scalar_one_or_none()

        if not student:
            return AuthResult(
                error_code="USERNAME_NOT_FOUND",
                error_message="No account found with this roll number",
            )
        if not student.is_active:
            return AuthResult(
                error_code="ACCOUNT_INACTIVE",
                error_message="Your account has been deactivated. Contact your admin",
            )
        # Check account lock
        if student.locked_until and student.locked_until > datetime.utcnow():
            return AuthResult(
                error_code="ACCOUNT_LOCKED",
                error_message="Account temporarily locked due to too many failed attempts. Try again later",
            )
        if not verify_password(password, student.hashed_password):
            # Increment failed attempts
            student.failed_login_attempts = (student.failed_login_attempts or 0) + 1
            db.add(student)
            await db.commit()
            return AuthResult(
                error_code="INVALID_PASSWORD",
                error_message="Incorrect password. Please try again",
            )

        # Reset failed attempts on success
        student.failed_login_attempts = 0
        student.last_login_at = datetime.utcnow()
        db.add(student)
        await db.commit()

        token = create_access_token(
            subject=student.roll_number,
            role=UserRole.STUDENT,
            extra_claims={
                "student_uuid": str(student.id),
                "must_change_password": student.must_change_password,
            },
        )
        return AuthResult(token=TokenResponse(
            access_token=token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=UserRole.STUDENT,
            subject_id=student.roll_number,
            roll_number=student.roll_number,
            student_uuid=str(student.id),
        ))

    @staticmethod
    async def login_mentor(
        username: str,
        password: str,
        db: AsyncSession,
    ) -> AuthResult:
        result = await db.execute(
            select(Mentor).where(Mentor.username == username)
        )
        mentor: Optional[Mentor] = result.scalar_one_or_none()

        if not mentor:
            return AuthResult(
                error_code="USERNAME_NOT_FOUND",
                error_message="No account found with this username",
            )
        if not mentor.is_active:
            return AuthResult(
                error_code="ACCOUNT_INACTIVE",
                error_message="Your account has been deactivated. Contact your admin",
            )
        if mentor.locked_until and mentor.locked_until > datetime.utcnow():
            return AuthResult(
                error_code="ACCOUNT_LOCKED",
                error_message="Account temporarily locked due to too many failed attempts. Try again later",
            )
        if not verify_password(password, mentor.hashed_password):
            mentor.failed_login_attempts = (mentor.failed_login_attempts or 0) + 1
            db.add(mentor)
            await db.commit()
            return AuthResult(
                error_code="INVALID_PASSWORD",
                error_message="Incorrect password. Please try again",
            )

        mentor.failed_login_attempts = 0
        mentor.last_login_at = datetime.utcnow()
        db.add(mentor)
        await db.commit()

        token = create_access_token(
            subject=mentor.username,
            role=mentor.role,
            extra_claims={"mentor_uuid": str(mentor.id)},
        )
        return AuthResult(token=TokenResponse(
            access_token=token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=mentor.role,
            subject_id=mentor.username,
            mentor_uuid=str(mentor.id),
        ))

    @staticmethod
    async def change_student_password(
        student: Student,
        current_password: str,
        new_password: str,
        db: AsyncSession,
    ) -> AuthResult:
        if not verify_password(current_password, student.hashed_password):
            return AuthResult(
                error_code="WRONG_CURRENT_PASSWORD",
                error_message="Current password is incorrect",
            )
        if verify_password(new_password, student.hashed_password):
            return AuthResult(
                error_code="SAME_AS_OLD_PASSWORD",
                error_message="New password must be different from current password",
            )
        if len(new_password) < 8:
            return AuthResult(
                error_code="WEAK_PASSWORD",
                error_message="Password must be at least 8 characters",
            )
        student.hashed_password = hash_password(new_password)
        student.must_change_password = False
        db.add(student)
        await db.commit()
        return AuthResult(token=None, error_code=None, error_message=None)

    @staticmethod
    async def change_mentor_password(
        mentor: Mentor,
        current_password: str,
        new_password: str,
        db: AsyncSession,
    ) -> AuthResult:
        if not verify_password(current_password, mentor.hashed_password):
            return AuthResult(
                error_code="WRONG_CURRENT_PASSWORD",
                error_message="Current password is incorrect",
            )
        if verify_password(new_password, mentor.hashed_password):
            return AuthResult(
                error_code="SAME_AS_OLD_PASSWORD",
                error_message="New password must be different from current password",
            )
        if len(new_password) < 8:
            return AuthResult(
                error_code="WEAK_PASSWORD",
                error_message="Password must be at least 8 characters",
            )
        mentor.hashed_password = hash_password(new_password)
        db.add(mentor)
        await db.commit()
        return AuthResult(token=None, error_code=None, error_message=None)
