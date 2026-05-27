import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint
from sqlmodel import Field, SQLModel, Column


# ── Enums ─────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    STUDENT = "student"
    MENTOR = "mentor"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    STARTED     = "STARTED"      # student picked an assignment, session opened
    IN_PROGRESS = "IN_PROGRESS"  # grader is running locally
    SUBMITTED   = "SUBMITTED"    # proof file received, pending verification
    COMPLETED   = "COMPLETED"    # proof verified, score computed and stored
    REJECTED    = "REJECTED"     # HMAC or SHA-256 check failed


class AssignmentCategory(str, Enum):
    ARTIFACT_VALIDATION      = "artifact_validation"
    DETERMINISTIC_EXECUTION  = "deterministic_execution"
    FILESYSTEM_VALIDATION    = "filesystem_validation"
    GIT_VALIDATION           = "git_validation"
    NETWORK_VALIDATION       = "network_validation"
    DOCUMENTATION_REVIEW     = "documentation_review"
    MANUAL_REVIEW            = "manual_review"


# ── Student ───────────────────────────────────────────────────────────

class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    roll_number: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False, index=True)
    )
    full_name: str = Field(sa_column=Column(String(200), nullable=False))
    email: str = Field(sa_column=Column(String(200), unique=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(200), nullable=False))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Mentor ────────────────────────────────────────────────────────────

class Mentor(SQLModel, table=True):
    __tablename__ = "mentors"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    username: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False, index=True)
    )
    full_name: str = Field(sa_column=Column(String(200), nullable=False))
    email: str = Field(sa_column=Column(String(200), unique=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(200), nullable=False))
    role: UserRole = Field(default=UserRole.MENTOR)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Assignment ────────────────────────────────────────────────────────

class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    slug: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False, index=True)
    )
    title: str = Field(sa_column=Column(String(300), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category: AssignmentCategory
    max_score: float = Field(default=100.0)
    deadline: Optional[datetime] = Field(default=None)
    is_published: bool = Field(default=False)
    created_by_id: uuid.UUID = Field(foreign_key="mentors.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Grading Session ───────────────────────────────────────────────────

class GradingSession(SQLModel, table=True):
    __tablename__ = "grading_sessions"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "assignment_id", "status",
            name="uq_active_session",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    status: SessionStatus = Field(default=SessionStatus.STARTED)

    # Timestamps
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Proof tracking
    proof_nonce: Optional[str] = Field(
        default=None, sa_column=Column(String(200), unique=True, nullable=True)
    )

    # Scoring
    final_score: Optional[float] = Field(default=None)
    score_breakdown: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )  # stored as JSON string

    # Rejection
    rejection_reason: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )


# ── Proof Submission (immutable audit record) ─────────────────────────

class ProofSubmission(SQLModel, table=True):
    __tablename__ = "proof_submissions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="grading_sessions.id", index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)

    nonce: str = Field(sa_column=Column(String(200), unique=True, nullable=False))
    grader_binary_hash: str = Field(sa_column=Column(String(64), nullable=False))
    raw_proof: str = Field(sa_column=Column(Text, nullable=False))  # full JSON

    hmac_valid: bool = Field(default=False)
    hashes_valid: bool = Field(default=False)
    final_score: Optional[float] = Field(default=None)

    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = Field(default=None)


# ── Nonce Registry (replay prevention) ───────────────────────────────

class UsedNonce(SQLModel, table=True):
    __tablename__ = "used_nonces"

    nonce: str = Field(
        sa_column=Column(String(200), primary_key=True, nullable=False)
    )
    student_id: uuid.UUID = Field(foreign_key="students.id")
    used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
