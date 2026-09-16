from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.property_search_intent import (
    PropertySearchIntent,
)


def test_property_search_intent_accepts_valid_data():
    intent = PropertySearchIntent(
        semantic_query=(
            "apartamento tranquilo com academia"
        ),
        neighborhood="Boa Vista",
        max_price=Decimal("700000.00"),
        min_bedrooms=3,
        min_usable_area=70,
    )

    assert intent.semantic_query == (
        "apartamento tranquilo com academia"
    )
    assert intent.neighborhood == "Boa Vista"
    assert intent.max_price == Decimal("700000.00")
    assert intent.min_bedrooms == 3
    assert intent.min_usable_area == 70

    assert intent.min_price is None
    assert intent.min_bathrooms is None
    assert intent.min_parking_spaces is None


def test_property_search_intent_rejects_negative_price():
    with pytest.raises(ValidationError):
        PropertySearchIntent(
            semantic_query="apartamento",
            max_price=Decimal("-1"),
        )


def test_property_search_intent_requires_semantic_query():
    with pytest.raises(ValidationError):
        PropertySearchIntent(
            semantic_query="",
        )