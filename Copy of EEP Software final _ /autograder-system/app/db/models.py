from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class UserRole(str, PyEnum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class SubmissionStatus(str, PyEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.student
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="user")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
