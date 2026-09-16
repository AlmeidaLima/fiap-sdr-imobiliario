from decimal import Decimal

from app.services.property_search_intent_service import (
    PropertySearchIntentService,
)


def test_parse_complete_property_search_intent():
    service = PropertySearchIntentService()

    intent = service.parse(
        "Quero um apartamento no Boa Vista "
        "com 3 quartos, 2 banheiros, 1 vaga, "
        "70 m², academia e churrasqueira, "
        "até 700 mil."
    )

    assert intent.neighborhood == "Boa Vista"
    assert intent.max_price == Decimal("700000")
    assert intent.min_bedrooms == 3
    assert intent.min_bathrooms == 2
    assert intent.min_parking_spaces == 1
    assert intent.min_usable_area == 70

    assert (
            "academia"
            in intent.semantic_query.lower()
    )

    assert (
            "churrasqueira"
            in intent.semantic_query.lower()
    )


def test_parse_partial_property_search_intent():
    service = PropertySearchIntentService()

    intent = service.parse(
        "Quero apartamento com 2 quartos "
        "e churrasqueira."
    )

    assert intent.neighborhood is None
    assert intent.max_price is None
    assert intent.min_bedrooms == 2
    assert intent.min_bathrooms is None
    assert intent.min_parking_spaces is None
    assert intent.min_usable_area is None


def test_parse_price_in_reais():
    service = PropertySearchIntentService()

    intent = service.parse(
        "Apartamento até R$ 650.000"
    )

    assert intent.max_price == Decimal("650000")


def test_parse_price_in_thousands():
    service = PropertySearchIntentService()

    intent = service.parse(
        "Apartamento até 550 mil"
    )

    assert intent.max_price == Decimal("550000")


def test_parse_keeps_subjective_preferences():
    service = PropertySearchIntentService()

    intent = service.parse(
        "Quero um apartamento tranquilo "
        "próximo a transporte público."
    )

    assert "tranquilo" in intent.semantic_query.lower()

    assert (
            "transporte público"
            in intent.semantic_query.lower()
    )