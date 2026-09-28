from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.conversation import ConversationState


class AppointmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: str = Field(min_length=1)


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    property_id: int | None
    appointment_type: Literal["VISITA", "REUNIAO"]
    scheduled_at: datetime
    status: Literal["CONFIRMED", "CANCELLED"]
    idempotency_key: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AppointmentCreateResponse(BaseModel):
    appointment: AppointmentResponse
    state: ConversationState
