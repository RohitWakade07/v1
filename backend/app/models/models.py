import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import String, Text


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class UserRole(str, Enum):
    STUDENT = "student"
    MENTOR = "mentor"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    CREATED = "CREATED"
    CHALLENGE_ISSUED = "CHALLENGE_ISSUED"
    EXECUTING = "EXECUTING"
    WAITING_HEARTBEAT = "WAITING_HEARTBEAT"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    EXPIRED = "EXPIRED"


class AssignmentCategory(str, Enum):
    ARTIFACT_VALIDATION = "artifact_validation"
    DETERMINISTIC_EXECUTION = "deterministic_execution"
    FILESYSTEM_VALIDATION = "filesystem_validation"
    GIT_VALIDATION = "git_validation"
    NETWORK_VALIDATION = "network_validation"
    DOCUMENTATION_REVIEW = "documentation_review"
    MANUAL_REVIEW = "manual_review"


# ─────────────────────────────────────────────
# Student
# ─────────────────────────────────────────────

class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    roll_number: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False, index=True)
    )
    full_name: str = Field(sa_column=Column(String(200), nullable=False))
    email: str = Field(sa_column=Column(String(200), unique=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(200), nullable=False))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────
# Mentor (faculty / TA / admin)
# ─────────────────────────────────────────────

class Mentor(SQLModel, table=True):
    __tablename__ = "mentors"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    username: str = Field(sa_column=Column(String(100), unique=True, nullable=False, index=True))
    full_name: str = Field(sa_column=Column(String(200), nullable=False))
    email: str = Field(sa_column=Column(String(200), unique=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(200), nullable=False))
    role: UserRole = Field(default=UserRole.MENTOR)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────
# Assignment
# ─────────────────────────────────────────────

class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    slug: str = Field(sa_column=Column(String(100), unique=True, nullable=False, index=True))
    title: str = Field(sa_column=Column(String(300), nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=True))
    category: AssignmentCategory
    deadline: Optional[datetime] = Field(default=None)
    is_published: bool = Field(default=False)
    created_by_id: uuid.UUID = Field(foreign_key="mentors.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────
# Grading Session
# ─────────────────────────────────────────────

class GradingSession(SQLModel, table=True):
    __tablename__ = "grading_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)

    status: SessionStatus = Field(default=SessionStatus.CREATED)

    # Heartbeat tracking
    last_heartbeat_at: Optional[datetime] = Field(default=None)
    last_sequence: int = Field(default=0)
    expected_sequence: int = Field(default=1)

    # Challenge binding
    nonce: Optional[str] = Field(default=None, sa_column=Column(String(200), nullable=True))
    challenge_issued_at: Optional[datetime] = Field(default=None)
    challenge_expires_at: Optional[datetime] = Field(default=None)

    # Scoring
    final_score: Optional[float] = Field(default=None)
    score_breakdown: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )  # JSON string

    # Anomaly flag
    anomaly_detected: bool = Field(default=False)
    anomaly_notes: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)


# ─────────────────────────────────────────────
# Heartbeat Log (immutable audit trail)
# ─────────────────────────────────────────────

class HeartbeatLog(SQLModel, table=True):
    __tablename__ = "heartbeat_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="grading_sessions.id", index=True)
    sequence: int
    phase: str = Field(sa_column=Column(String(100)))
    stdout_hash: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    stderr_hash: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    artifact_hashes: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )  # JSON array string
    decision: str = Field(default="continue", sa_column=Column(String(20)))
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
