from datetime import datetime
from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    assignment_id: int = Field(..., gt=0)
    language: str = Field(..., min_length=2, max_length=50)
    code: str = Field(..., min_length=1)


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    assignment_id: int
    language: str
    status: str
    score: float | None = None
    feedback: str | None = None
    logs: str | None = None
    execution_time_ms: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubmissionQueuedResponse(BaseModel):
    message: str
    submission_id: int
    status: str
