from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.lead_handoff import LeadHandoffResponse


class DashboardLeadSummary(BaseModel):
    lead_id: int
    conversation_id: str
    name: str | None
    status: str
    commercial_intent: Literal[
        "COMPRA", "ALUGUEL", "INVESTIMENTO", "INDEFINIDO",
    ] | None
    score: int = Field(ge=0, le=100)
    classification: Literal["FRIO", "MORNO", "QUENTE"]
    last_interaction_at: datetime | None


class DashboardLeadListResponse(BaseModel):
    leads: list[DashboardLeadSummary] = Field(default_factory=list)


class DashboardPreferences(BaseModel):
    urgency_days: int | None
    neighborhood: str | None
    min_price: Decimal | None
    max_price: Decimal | None
    min_bedrooms: int | None
    min_bathrooms: int | None
    min_parking_spaces: int | None
    min_usable_area: int | None
    semantic_preferences: list[str] = Field(default_factory=list)


class DashboardMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class DashboardProperty(BaseModel):
    id: int
    external_id: str
    title: str | None
    description: str | None
    neighborhood: str
    price: Decimal
    bedrooms: int
    bathrooms: int
    parking_spaces: int | None
    usable_area: int


class DashboardAppointment(BaseModel):
    id: int
    property_id: int | None
    appointment_type: Literal["VISITA", "REUNIAO"]
    scheduled_at: datetime
    status: Literal["CONFIRMED", "CANCELLED"]
    notes: str | None
    created_at: datetime
    updated_at: datetime


class DashboardLeadDetailResponse(BaseModel):
    lead: DashboardLeadSummary
    preferences: DashboardPreferences
    history: list[DashboardMessage] = Field(default_factory=list)
    recommended_properties: list[DashboardProperty] = Field(
        default_factory=list,
    )
    selected_property: DashboardProperty | None
    summary: LeadHandoffResponse
    appointments: list[DashboardAppointment] = Field(default_factory=list)
