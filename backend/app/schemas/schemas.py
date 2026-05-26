import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models.models import SessionStatus, UserRole


# ─────────────────────────────────────────────
# Auth schemas
# ─────────────────────────────────────────────

class StudentLoginRequest(BaseModel):
    roll_number: str
    password: str


class MentorLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    role: UserRole
    subject_id: str  # roll_number or username


# ─────────────────────────────────────────────
# Student schemas
# ─────────────────────────────────────────────

class StudentCreate(BaseModel):
    roll_number: str
    full_name: str
    email: EmailStr
    password: str

    @field_validator("roll_number")
    @classmethod
    def roll_number_format(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("Roll number too short")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
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


# ─────────────────────────────────────────────
# Session schemas
# ─────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    assignment_id: uuid.UUID


class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    created_at: datetime


class SessionStatusResponse(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    last_sequence: int
    expected_sequence: int
    last_heartbeat_at: Optional[datetime]
    anomaly_detected: bool


# ─────────────────────────────────────────────
# Heartbeat schemas
# ─────────────────────────────────────────────

class HeartbeatRequest(BaseModel):
    session_id: uuid.UUID
    nonce: str
    sequence: int
    phase: str
    stdout_hash: Optional[str] = None
    stderr_hash: Optional[str] = None
    artifact_hashes: Optional[list[str]] = None

    @field_validator("sequence")
    @classmethod
    def sequence_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Sequence must be >= 1")
        return v

    @field_validator("phase")
    @classmethod
    def phase_valid(cls, v: str) -> str:
        allowed = {"authentication", "execution", "validation", "finalization"}
        if v not in allowed:
            raise ValueError(f"Phase must be one of {allowed}")
        return v


class HeartbeatResponse(BaseModel):
    decision: str          # "continue" | "terminate"
    reason: Optional[str]  # populated on terminate
    next_expected_sequence: int


# ─────────────────────────────────────────────
# Finalization schemas
# ─────────────────────────────────────────────

class FinalizeRequest(BaseModel):
    session_id: uuid.UUID
    final_sequence: int


class FinalizeResponse(BaseModel):
    session_id: uuid.UUID
    status: SessionStatus
    final_score: Optional[float]
    message: str


# ─────────────────────────────────────────────
# Common error schema
# ─────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
