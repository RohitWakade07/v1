import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any, List

from sqlalchemy import String, Text, Integer, UniqueConstraint, Index, Float
from sqlalchemy.dialects.postgresql import JSONB
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


# Sessions that represent a finished, gradable outcome for results/analytics views.
COMPLETED_RESULT_STATUSES = (
    SessionStatus.VERIFIED,
    SessionStatus.COMPLETED,
)


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
    must_change_password: bool = Field(default=False)
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    last_login_at: Optional[datetime] = Field(default=None)
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
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    last_login_at: Optional[datetime] = Field(default=None)
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
    # Resource links: list of {title: str, url: str} stored as JSON
    resource_links: Any = Field(default=[], sa_column=Column(JSONB, nullable=False, server_default='[]'))
    # Late submission penalty as a percentage (0-100)
    late_penalty_pct: float = Field(default=0.0, sa_column=Column(Float, nullable=False, server_default="0.0"))
    # Submission info fields (editable by admin)
    submission_filename: Optional[str] = Field(default=None, sa_column=Column(String(300), nullable=True))
    submission_instructions: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
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

    # CLI uploaded payload
    pending_payload: Optional[str] = Field(
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


# ── Notification (polymorphic, rebuilt) ──────────────────────────────

class RecipientType(str, Enum):
    STUDENT = "student"
    MENTOR = "mentor"


class NotificationSourceType(str, Enum):
    ANNOUNCEMENT = "announcement"
    SUBMISSION = "submission"
    QUIZ = "quiz"
    SYSTEM = "system"


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    recipient_id: uuid.UUID = Field(index=True)  # student.id or mentor.id
    recipient_type: str = Field(sa_column=Column(String(20), nullable=False))
    source_type: str = Field(sa_column=Column(String(20), nullable=False, server_default="system"))
    source_id: Optional[uuid.UUID] = Field(default=None)  # announcement.id, submission.id, etc.
    title: str = Field(sa_column=Column(String(300), nullable=False))
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


class SubmissionSourceType(str, Enum):
    GITHUB = "github"
    ZIP = "zip"


class SubmissionStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class Submission(SQLModel, table=True):
    __tablename__ = "submissions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    status: SubmissionStatus = Field(default=SubmissionStatus.PENDING)
    source_type: SubmissionSourceType = Field(default=SubmissionSourceType.ZIP)
    repo_url: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    zip_object_key: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    score: Optional[float] = Field(default=None)
    max_score: Optional[float] = Field(default=None)
    passed: Optional[bool] = Field(default=None)
    attempt_number: int = Field(default=1)
    worker_id: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    validation_error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SubmissionResult(SQLModel, table=True):
    __tablename__ = "submission_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    submission_id: uuid.UUID = Field(foreign_key="submissions.id", unique=True, index=True)
    checks_json: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    feedback: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    stdout: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    stderr: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    execution_command: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    exit_code: Optional[int] = Field(default=None)
    execution_time_ms: Optional[int] = Field(default=None)
    timed_out: bool = Field(default=False)
    oom_killed: bool = Field(default=False)
    container_id: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    grader_logs: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    ai_feedback: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Celery Grading Pipeline ───────────────────────────────────────────
# The following models support the transactional outbox + Celery worker pipeline.


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


class SubmissionOutbox(SQLModel, table=True):
    __tablename__ = "submission_outbox"

    id: int = Field(default=None, primary_key=True)
    submission_id: uuid.UUID = Field(foreign_key="submissions.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    dispatched_at: Optional[datetime] = Field(default=None, index=True)
    retry_count: int = Field(default=0)
    payload: str = Field(sa_column=Column(Text, nullable=False))


class JobStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class GradingJob(SQLModel, table=True):
    __tablename__ = "grading_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    submission_id: uuid.UUID = Field(foreign_key="submissions.id", unique=True, index=True)
    status: JobStatus = Field(default=JobStatus.PENDING, index=True)
    worker_id: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    celery_task_id: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    attempt_count: int = Field(default=0)
    max_attempts: int = Field(default=3)
    queue_name: str = Field(default="normal", sa_column=Column(String(50)))


class ExecutionMetrics(SQLModel, table=True):
    __tablename__ = "execution_metrics"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    submission_id: uuid.UUID = Field(foreign_key="submissions.id", unique=True, index=True)
    container_id: str = Field(sa_column=Column(String(100), nullable=False))
    wall_time_ms: int = Field(default=0)
    cpu_time_ms: int = Field(default=0)
    peak_memory_mb: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionLogs(SQLModel, table=True):
    __tablename__ = "execution_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    submission_id: uuid.UUID = Field(foreign_key="submissions.id", index=True)
    log_level: str = Field(sa_column=Column(String(20), nullable=False))
    message: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Submission Rate Limit ─────────────────────────────────────────────

class SubmissionRateLimit(SQLModel, table=True):
    __tablename__ = "submission_rate_limits"
    __table_args__ = (
        UniqueConstraint("student_id", "assignment_id", name="uq_rate_limit_student_assignment"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True)
    last_submitted_at: datetime = Field(default_factory=datetime.utcnow)


# ── Quiz ─────────────────────────────────────────────────────────────

class QuestionType(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class Quiz(SQLModel, table=True):
    __tablename__ = "quizzes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    assignment_id: uuid.UUID = Field(foreign_key="assignments.id", index=True, unique=True)
    title: str = Field(sa_column=Column(String(300), nullable=False))
    marks_per_question: int = Field(default=1)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuizQuestion(SQLModel, table=True):
    __tablename__ = "quiz_questions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    quiz_id: uuid.UUID = Field(foreign_key="quizzes.id", index=True)
    question_text: str = Field(sa_column=Column(Text, nullable=False))
    type: str = Field(sa_column=Column(String(20), nullable=False, server_default="single"))
    marks: Optional[int] = Field(default=None)  # overrides quiz.marks_per_question if set
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizOption(SQLModel, table=True):
    __tablename__ = "quiz_options"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    question_id: uuid.UUID = Field(foreign_key="quiz_questions.id", index=True)
    option_text: str = Field(sa_column=Column(Text, nullable=False))
    is_correct: bool = Field(default=False)
    order_index: int = Field(default=0)


class QuizAttempt(SQLModel, table=True):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        UniqueConstraint("quiz_id", "student_id", name="uq_one_attempt_per_student"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    quiz_id: uuid.UUID = Field(foreign_key="quizzes.id", index=True)
    student_id: uuid.UUID = Field(foreign_key="students.id", index=True)
    total_score: int = Field(default=0)
    max_score: int = Field(default=0)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = Field(default=None)


class QuizAnswer(SQLModel, table=True):
    __tablename__ = "quiz_answers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    attempt_id: uuid.UUID = Field(foreign_key="quiz_attempts.id", index=True)
    question_id: uuid.UUID = Field(foreign_key="quiz_questions.id")
    is_correct: bool = Field(default=False)
    marks_awarded: int = Field(default=0)


class QuizAnswerOption(SQLModel, table=True):
    __tablename__ = "quiz_answer_options"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    answer_id: uuid.UUID = Field(foreign_key="quiz_answers.id")
    option_id: uuid.UUID = Field(foreign_key="quiz_options.id")


# ── Announcements ─────────────────────────────────────────────────────

class AudienceType(str, Enum):
    STUDENTS = "students"
    MENTORS = "mentors"
    ALL = "all"


class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    admin_id: uuid.UUID = Field(foreign_key="mentors.id", index=True)
    title: str = Field(sa_column=Column(String(300), nullable=False))
    body: str = Field(sa_column=Column(Text, nullable=False))
    audience: str = Field(sa_column=Column(String(20), default="all"))
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AnnouncementRead(SQLModel, table=True):
    __tablename__ = "announcement_reads"
    __table_args__ = (
        UniqueConstraint("announcement_id", "user_id", name="uq_announcement_read"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    announcement_id: uuid.UUID = Field(foreign_key="announcements.id", index=True)
    user_id: uuid.UUID = Field(index=True)  # student.id or mentor.id
    read_at: datetime = Field(default_factory=datetime.utcnow)
