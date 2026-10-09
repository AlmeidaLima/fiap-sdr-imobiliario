from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LeadFollowUpCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_id: int = Field(gt=0)
    scheduled_at: datetime
    appointment_id: int | None = Field(
        default=None,
        gt=0,
    )


class LeadFollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    appointment_id: int | None
    status: Literal[
        "PENDING",
        "COMPLETED",
        "CANCELLED",
    ]
    scheduled_at: datetime
    completed_at: datetime | None
    attempt_count: int
    idempotency_key: str
    created_at: datetime
    updated_at: datetime


class LeadFollowUpAttemptCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Literal[
        "MANUAL",
        "EMAIL",
        "WHATSAPP",
        "WEB",
    ]
    status: Literal[
        "SUCCESS",
        "FAILED",
    ]
    message: str | None = None


class LeadFollowUpAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    follow_up_id: int
    attempt_number: int
    channel: Literal[
        "MANUAL",
        "EMAIL",
        "WHATSAPP",
        "WEB",
    ]
    status: Literal[
        "SUCCESS",
        "FAILED",
    ]
    message: str | None
    executed_at: datetime
    created_at: datetime
