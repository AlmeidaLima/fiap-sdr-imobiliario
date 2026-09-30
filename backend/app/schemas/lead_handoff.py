from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class LeadHandoffLead(BaseModel):
    id: int
    name: str | None
    score: int
    classification: Literal["FRIO", "MORNO", "QUENTE"]


class LeadHandoffQualification(BaseModel):
    commercial_intent: Literal[
        "COMPRA", "ALUGUEL", "INVESTIMENTO", "INDEFINIDO",
    ] | None
    urgency_days: int | None
    neighborhood: str | None
    min_price: Decimal | None
    max_price: Decimal | None
    min_bedrooms: int | None
    min_bathrooms: int | None
    min_parking_spaces: int | None
    min_usable_area: int | None


class LeadHandoffProperty(BaseModel):
    id: int
    external_id: str
    title: str | None
    neighborhood: str
    price: Decimal
    bedrooms: int
    bathrooms: int
    parking_spaces: int | None
    usable_area: int


class LeadHandoffAppointment(BaseModel):
    id: int
    appointment_type: Literal["VISITA", "REUNIAO"]
    scheduled_at: datetime
    status: Literal["CONFIRMED", "CANCELLED"]


class LeadHandoffResponse(BaseModel):
    conversation_id: str
    handoff_status: Literal["READY", "NOT_READY"]
    lead: LeadHandoffLead | None
    qualification: LeadHandoffQualification
    property: LeadHandoffProperty | None
    appointment: LeadHandoffAppointment | None
