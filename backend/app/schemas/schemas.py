import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.models import SessionStatus, UserRole, AssignmentCategory


# ── Auth ──────────────────────────────────────────────────────────────

class StudentLoginRequest(BaseModel):
    roll_number: str
    password: str


class MentorLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole
    subject_id: str
    roll_number: Optional[str] = None
    student_uuid: Optional[str] = None
    mentor_uuid: Optional[str] = None


# ── Student ───────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    roll_number: str
    full_name: str
    email: EmailStr
    password: str
    class_code: Optional[str] = None

    @field_validator("roll_number")
    @classmethod
    def normalise_roll(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("Roll number too short")
        return v

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class StudentPublic(BaseModel):
    id: uuid.UUID
    roll_number: str
    full_name: str
    email: str
    is_active: bool
    created_at: datetime


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str
    email: str
    roll_number: str
    student_uuid: uuid.UUID
    role: UserRole = UserRole.STUDENT
    classroom_name: Optional[str] = None
    classroom_status: Optional[str] = None
    mentor_name: Optional[str] = None



# ── Assignment ────────────────────────────────────────────────────────

class AssignmentPublic(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: Optional[str]
    category: AssignmentCategory
    max_score: float
    deadline: Optional[datetime]
    is_published: bool
    is_archived: bool
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class AssignmentCreate(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    category: AssignmentCategory
    max_score: float = 100.0
    deadline: Optional[datetime] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[float] = None
    deadline: Optional[datetime] = None


# ── Session ───────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    assignment_id: uuid.UUID


class EvaluatorSessionCreateRequest(BaseModel):
    student_roll: str
    assignment_slug: str


class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    assignment_id: uuid.UUID
    assignment_title: str
    status: SessionStatus
    started_at: datetime


class SessionStatusResponse(BaseModel):
    session_id: uuid.UUID
    assignment_id: uuid.UUID
    status: SessionStatus
    started_at: datetime
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    final_score: Optional[float]
    rejection_reason: Optional[str]


# ── Proof submission ──────────────────────────────────────────────────

class TestResult(BaseModel):
    test_id: str
    passed: bool
    stdout_hash: Optional[str] = None
    stderr_hash: Optional[str] = None
    exit_code: int = 0
    score: float = 0.0


class ProofSubmitRequest(BaseModel):
    session_id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: str           # roll_number — cross-checked against JWT
    timestamp: str            # ISO8601
    nonce: str                # UUID — single use, replay prevention
    grader_binary_hash: str   # SHA-256 of the grader binary itself
    results: dict[str, TestResult]
    artifact_hashes: dict[str, str]  # filename -> sha256
    hmac_signature: str       # HMAC-SHA256 over entire payload minus this field


class ProofSubmitResponse(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    final_score: Optional[float]
    message: str


# ── Mentor Portal Phase 2 ──────────────────────────────────────────────

class MentorStudentPublic(BaseModel):
    id: uuid.UUID
    roll_number: str
    full_name: str
    email: str
    assignments_participated: int
    sessions_count: int


class MentorSessionPublic(BaseModel):
    id: uuid.UUID
    student_roll: str
    student_name: str
    assignment_slug: str
    assignment_title: str
    status: SessionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    final_score: Optional[float]


class MentorResultPublic(BaseModel):
    session_id: uuid.UUID
    student_roll: str
    student_name: str
    assignment_slug: str
    assignment_title: str
    final_score: float
    max_score: float
    completed_at: datetime


class MentorAnalyticsSummary(BaseModel):
    total_students: int
    completion_rate: float
    avg_score: float
    total_submissions: int
    score_distribution: dict[str, int]
    assignments_participation: dict[str, int]
    category_breakdown: dict[str, int]


# ── Grader ────────────────────────────────────────────────────────────

class GraderPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    created_at: datetime


class GraderVersionPublic(BaseModel):
    id: uuid.UUID
    grader_id: uuid.UUID
    version: str
    binary_hash: str
    created_at: datetime


# ── Evaluator Build ───────────────────────────────────────────────────

class EvaluatorBuildPublic(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    mentor_id: uuid.UUID
    status: str
    binary_hash: Optional[str]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]


# ── Notification ──────────────────────────────────────────────────────

class NotificationPublic(BaseModel):
    id: uuid.UUID
    mentor_id: uuid.UUID
    title: str
    message: str
    is_read: bool
    created_at: datetime


# ── Assignment Config ─────────────────────────────────────────────────

class AssignmentConfigPublic(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    config_data: str
    created_at: datetime
    updated_at: datetime


class AssignmentConfigUpdate(BaseModel):
    config_data: str


# ── Error ─────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


# ── Challenge package retrieval schemas ────────────────────────────────

class ChallengeSessionMetadata(BaseModel):
    session_id: uuid.UUID
    student_id: str           # roll_number
    nonce: str                # proof_nonce
    started_at: datetime


class ChallengeAssignmentMetadata(BaseModel):
    assignment_id: uuid.UUID
    slug: str
    title: str
    category: AssignmentCategory
    max_score: float
    deadline: Optional[datetime] = None


class ChallengeGraderMetadata(BaseModel):
    grader_id: uuid.UUID
    name: str
    version: str
    binary_hash: str


class ChallengePackageResponse(BaseModel):
    session: ChallengeSessionMetadata
    assignment: ChallengeAssignmentMetadata
    grader: ChallengeGraderMetadata
    execution_constraints: dict
    validation_rules: list[dict]


# ── Results & Certificates Public views ────────────────────────────────

class FinalResultPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    student_id: uuid.UUID
    assignment_id: uuid.UUID
    score: float
    passed: bool
    score_breakdown: Optional[str] = None
    verified_at: datetime


class CertificatePublic(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    assignment_id: uuid.UUID
    final_result_id: uuid.UUID
    certificate_code: str
    issued_at: datetime


# ── Classroom DTOs ────────────────────────────────────────────────────

class ClassroomCreate(BaseModel):
    name: str


class ClassroomPublic(BaseModel):
    id: uuid.UUID
    name: str
    class_code: str
    mentor_id: uuid.UUID
    created_at: datetime


class ClassroomJoinRequest(BaseModel):
    class_code: str


class ClassroomStudentEnrollmentResponse(BaseModel):
    enrollment_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_roll: str
    student_email: str
    status: str
    joined_at: datetime

