from decimal import Decimal

from pydantic import BaseModel, Field


class PropertySearchIntent(BaseModel):
    semantic_query: str = Field(
        ...,
        min_length=1,
        description=(
            "Preferências do cliente utilizadas "
            "na busca semântica."
        ),
    )

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

class PropertyNaturalLanguageSearchRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=3,
        description=(
            "Descrição em linguagem natural "
            "do imóvel desejado pelo cliente."
        ),
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )