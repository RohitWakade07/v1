import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

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


# ── Student ───────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    roll_number: str
    full_name: str
    email: EmailStr
    password: str

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


# ── Assignment ────────────────────────────────────────────────────────

class AssignmentPublic(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: Optional[str]
    category: AssignmentCategory
    max_score: float
    deadline: Optional[datetime]


class AssignmentCreate(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    category: AssignmentCategory
    max_score: float = 100.0
    deadline: Optional[datetime] = None


# ── Session ───────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    assignment_id: uuid.UUID


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


# ── Error ─────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
