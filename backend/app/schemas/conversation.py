from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.property import PropertySearchResponse


class ConversationState(BaseModel):
    conversation_id: str

    lead_name: str | None = None

    commercial_intent: Literal[
        "COMPRA", "ALUGUEL", "INVESTIMENTO", "INDEFINIDO",
    ] | None = None

    urgency_days: int | None = Field(default=None, ge=1)

    accepted_meeting_or_visit: bool = False

    lead_score: int = Field(default=0, ge=0, le=100)

    lead_classification: Literal[
        "FRIO", "MORNO", "QUENTE",
    ] = "FRIO"

    neighborhood: str | None = None

    min_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    max_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    min_bedrooms: int | None = Field(
        default=None,
        ge=0,
    )

    min_bathrooms: int | None = Field(
        default=None,
        ge=0,
    )

    min_parking_spaces: int | None = Field(
        default=None,
        ge=0,
    )

    min_usable_area: int | None = Field(
        default=None,
        ge=0,
    )

    semantic_preferences: list[str] = Field(
        default_factory=list,
    )


class ConversationQualification(BaseModel):
    qualified: bool

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    next_question: str | None = None


class LeadScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)

    classification: Literal[
        "FRIO", "MORNO", "QUENTE",
    ]


class ConversationTurnResult(BaseModel):
    state: ConversationState

    qualification: ConversationQualification

    properties: list = Field(
        default_factory=list,
    )

    response: str


class ConversationTurnRequest(BaseModel):
    conversation_id: str = Field(
        ...,
        min_length=1,
    )

    message: str = Field(
        ...,
        min_length=3,
    )

    state: ConversationState | None = None

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class ConversationTurnResponse(BaseModel):
    conversation_id: str

    response: str

    state: ConversationState

    qualification: ConversationQualification

    properties: list[PropertySearchResponse] = Field(
        default_factory=list,
    )
