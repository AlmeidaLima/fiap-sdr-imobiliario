from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.property import PropertySearchResponse


class ConversationState(BaseModel):
    conversation_id: str

    lead_name: str | None = None

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


class ConversationTurnResult(BaseModel):
    state: ConversationState

    qualification: ConversationQualification

    properties: list = Field(
        default_factory=list,
    )


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

    state: ConversationState

    qualification: ConversationQualification

    properties: list[PropertySearchResponse] = Field(
        default_factory=list,
    )