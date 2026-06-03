import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint, Index
from sqlmodel import Field, SQLModel, Column


# ── Enums ─────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    STUDENT = "student"
    MENTOR  = "mentor"
    ADMIN   = "admin"


class SessionStatus(str, Enum):
    # New 8-state lifecycle
    CREATED          = "CREATED"
    CHALLENGE_ISSUED = "CHALLENGE_ISSUED"
    RUNNING          = "RUNNING"
    ABORTED          = "ABORTED"
    PROOF_GENERATED  = "PROOF_GENERATED"
    PROOF_SUBMITTED  = "PROOF_SUBMITTED"
    VERIFIED         = "VERIFIED"
    FAILED           = "FAILED"

    # Legacy statuses for backward compatibility
    STARTED     = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED   = "SUBMITTED"
    COMPLETED   = "COMPLETED"
    REJECTED    = "REJECTED"


class GraderStatus(str, Enum):
    DRAFT    = "DRAFT"
    ACTIVE   = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class EvaluatorStatus(str, Enum):
    PENDING  = "PENDING"
    BUILDING = "BUILDING"
    SUCCESS  = "SUCCESS"
    FAILED   = "FAILED"


class AssignmentCategory(str, Enum):
    ARTIFACT_VALIDATION     = "artifact_validation"
    DETERMINISTIC_EXECUTION = "deterministic_execution"
    FILESYSTEM_VALIDATION   = "filesystem_validation"
    GIT_VALIDATION          = "git_validation"
    NETWORK_VALIDATION      = "network_validation"
    DOCUMENTATION_REVIEW    = "documentation_review"
    MANUAL_REVIEW           = "manual_review"


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    is_archived: bool = Field(default=False)
    created_by_id: uuid.UUID = Field(foreign_key="mentors.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Grading Session ───────────────────────────────────────────────────

# DB SCHEMA FIX:
# The original constraint was:
#   UniqueConstraint("student_id", "assignment_id", "status")
#
# This is BROKEN because:
#   - A student submits attempt 1 → COMPLETED   (row inserted, status=COMPLETED)
#   - A student submits attempt 2 → COMPLETED   (BLOCKED by the constraint!)
#   - The constraint allows only ONE row per (student, assignment, status) tuple.
#   - So a student can never achieve COMPLETED twice for the same assignment,
#     even if a new session was legitimately opened.
#   - It also means only one REJECTED row per student+assignment is possible.
#
# The CORRECT intent is: a student should not have more than one ACTIVE
# (STARTED or IN_PROGRESS) session for the same assignment simultaneously.
# COMPLETED and REJECTED sessions are historical records — many are allowed.
#
# Fix: remove the multi-column constraint entirely and enforce the "no duplicate
# active session" rule in SessionService.create_session() via a SELECT query
# (already correctly implemented there). A partial unique index covering only
# the active statuses is the right DB-level guard — added below.

class GradingSession(SQLModel, table=True):
    __tablename__ = "grading_sessions"

    # REMOVED: UniqueConstraint("student_id", "assignment_id", "status")
    # REASON:  Blocked legitimate multiple COMPLETED/REJECTED rows for the
    #          same student+assignment. See comment above.
    #
    # The active-session guard is enforced at the service layer in
    # SessionService.create_session() with a SELECT WHERE status IN
    # (STARTED, IN_PROGRESS). The partial index below adds a DB-level
    # guard as a safety net for the two active statuses only.
    __table_args__ = (
        Index(
            "ix_one_active_session_per_student_assignment",
            "student_id",
            "assignment_id",
            # postgresql_where clause — only enforced for active rows.
            # This prevents two concurrent active sessions at the DB level
            # without blocking historical COMPLETED/REJECTED records.
            # NOTE: This is a PostgreSQL-specific partial index.
            # For other databases, rely solely on the service-layer check.
            postgresql_where=(
                # Import done inline to avoid circular at module load time.
                # SQLAlchemy text() used for the partial index predicate.
                __import__('sqlalchemy').text(
                    "status IN ('CREATED', 'CHALLENGE_ISSUED', 'RUNNING', 'PROOF_GENERATED', 'STARTED', 'IN_PROGRESS')"
                )
            ),
            unique=True,
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    status: SessionStatus = Field(default=SessionStatus.STARTED)

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
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
    )

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
    raw_proof: str = Field(sa_column=Column(Text, nullable=False))

    hmac_valid: bool = Field(default=False)
    hashes_valid: bool = Field(default=False)
    final_score: Optional[float] = Field(default=None)

    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = Field(default=None)


# ── Nonce Registry (replay prevention) ───────────────────────────────

class UsedNonce(SQLModel, table=True):
    __tablename__ = "used_nonces"

    nonce: str = Field(
        sa_column=Column(String(200), primary_key=True, nullable=False)
    )
    student_id: uuid.UUID = Field(foreign_key="students.id")
    used_at: datetime = Field(default_factory=datetime.utcnow)


# ── Grader ────────────────────────────────────────────────────────────

class Grader(SQLModel, table=True):
    __tablename__ = "graders"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(sa_column=Column(String(200), unique=True, nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: GraderStatus = Field(default=GraderStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GraderVersion(SQLModel, table=True):
    __tablename__ = "grader_versions"
    __table_args__ = (
        UniqueConstraint("grader_id", "version", name="uq_grader_version"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    grader_id: uuid.UUID = Field(foreign_key="graders.id", index=True)
    version: str = Field(sa_column=Column(String(50), nullable=False))
    binary_hash: str = Field(sa_column=Column(String(64), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Assignment Config ─────────────────────────────────────────────────

class AssignmentConfig(SQLModel, table=True):
    __tablename__ = "assignment_configs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", unique=True, index=True)
    config_data: str = Field(default="{}", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Assignment Grader Mapping ─────────────────────────────────────────

class AssignmentGraderMapping(SQLModel, table=True):
    __tablename__ = "assignment_grader_mappings"
    __table_args__ = (
        UniqueConstraint("assignment_id", "grader_id", name="uq_assignment_grader"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    grader_id: uuid.UUID = Field(foreign_key="graders.id", index=True)
    grader_version_id: Optional[uuid.UUID] = Field(default=None, foreign_key="grader_versions.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Evaluator Build ───────────────────────────────────────────────────

class EvaluatorBuild(SQLModel, table=True):
    __tablename__ = "evaluator_builds"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    mentor_id: uuid.UUID = Field(foreign_key="mentors.id")
    status: EvaluatorStatus = Field(default=EvaluatorStatus.PENDING)
    binary_hash: Optional[str] = Field(default=None, sa_column=Column(String(64)))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


# ── Notification ──────────────────────────────────────────────────────

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    mentor_id: uuid.UUID = Field(foreign_key="mentors.id", index=True)
    title: str = Field(sa_column=Column(String(200), nullable=False))
    message: str = Field(sa_column=Column(Text, nullable=False))
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Final Result (persisted completion grade) ─────────────────────────

class FinalResult(SQLModel, table=True):
    __tablename__ = "final_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    session_id: uuid.UUID = Field(foreign_key="grading_sessions.id", index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    score: float = Field(default=0.0)
    passed: bool = Field(default=False)
    score_breakdown: Optional[str] = Field(default=None, sa_column=Column(Text))
    verified_at: datetime = Field(default_factory=datetime.utcnow)


# ── Certificate (academic recognition) ───────────────────────────────

class Certificate(SQLModel, table=True):
    __tablename__ = "certificates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    final_result_id: uuid.UUID = Field(foreign_key="final_results.id", index=True)
    certificate_code: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False, index=True)
    )
    issued_at: datetime = Field(default_factory=datetime.utcnow)


class Classroom(SQLModel, table=True):
    __tablename__ = "classrooms"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(sa_column=Column(String(200), nullable=False))
    class_code: str = Field(sa_column=Column(String(50), unique=True, nullable=False, index=True))
    mentor_id: uuid.UUID = Field(foreign_key="mentors.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClassroomEnrollment(SQLModel, table=True):
    __tablename__ = "classroom_enrollments"
    __table_args__ = (
        UniqueConstraint("classroom_id", "student_id", name="uq_classroom_student"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    classroom_id: uuid.UUID = Field(foreign_key="classrooms.id", index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    status: str = Field(default="PENDING")  # PENDING, APPROVED, REJECTED
    joined_at: datetime = Field(default_factory=datetime.utcnow)

