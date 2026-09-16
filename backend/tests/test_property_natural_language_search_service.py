from decimal import Decimal
from unittest.mock import Mock

from app.services.property_natural_language_search_service import (
    PropertyNaturalLanguageSearchService,
)
from app.services.property_search_intent_service import (
    PropertySearchIntentService,
)


def test_natural_language_search_delegates_intent_to_hybrid_search():
    intent_service = PropertySearchIntentService()

    hybrid_search_service = Mock()

    hybrid_search_service.search.return_value = [
        ("property-result", 0.91)
    ]

    service = PropertyNaturalLanguageSearchService(
        intent_service=intent_service,
        hybrid_search_service=hybrid_search_service,
    )

    results = service.search(
        message=(
            "Quero um apartamento no Boa Vista "
            "com 3 quartos, 2 banheiros, "
            "1 vaga e 70 m², até 700 mil. "
            "Gostaria de academia e churrasqueira."
        ),
        limit=5,
    )

    assert results == [
        ("property-result", 0.91)
    ]

    hybrid_search_service.search.assert_called_once()

    call_arguments = (
        hybrid_search_service.search.call_args.kwargs
    )

    assert (
            call_arguments["neighborhood"]
            == "Boa Vista"
    )

    assert (
            call_arguments["max_price"]
            == Decimal("700000")
    )

    assert call_arguments["min_bedrooms"] == 3
    assert call_arguments["min_bathrooms"] == 2
    assert call_arguments["min_parking_spaces"] == 1
    assert call_arguments["min_usable_area"] == 70
    assert call_arguments["available"] is True
    assert call_arguments["limit"] == 5

    assert (
            "academia"
            in call_arguments["query"].lower()
    )

    assert (
            "churrasqueira"
            in call_arguments["query"].lower()
    )