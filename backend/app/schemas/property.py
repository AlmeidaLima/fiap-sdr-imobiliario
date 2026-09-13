from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PropertyBase(BaseModel):
    external_id: str

    title: str | None = None
    description: str | None = None

    usable_area: int
    total_area: Decimal | None = None

    suites: int | None = None
    bathrooms: int
    bedrooms: int
    parking_spaces: int | None = None

    amenities: list[Any] = Field(default_factory=list)

    zip_code: str

    longitude: Decimal | None = None
    latitude: Decimal | None = None

    street: str | None = None
    neighborhood: str

    pois: list[Any] = Field(default_factory=list)

    yearly_iptu: Decimal | None = None
    monthly_condo_fee: Decimal | None = None

    price: Decimal

    source: str = "curitiba_kaggle"
    available: bool = True


class PropertyCreate(PropertyBase):
    pass


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )