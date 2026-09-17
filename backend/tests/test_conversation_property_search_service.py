from decimal import Decimal
from unittest.mock import Mock

from app.schemas.conversation import ConversationState
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)


def test_search_converts_conversation_state_to_hybrid_search():
    hybrid_search_service = Mock()

    hybrid_search_service.search.return_value = [
        "property-1",
        "property-2",
    ]

    service = ConversationPropertySearchService(
        hybrid_search_service=hybrid_search_service,
    )

    state = ConversationState(
        conversation_id="search-001",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
        min_usable_area=70,
        semantic_preferences=[
            "academia",
            "churrasqueira",
        ],
    )

    result = service.search(
        state,
        limit=5,
    )

    assert result == [
        "property-1",
        "property-2",
    ]

    hybrid_search_service.search.assert_called_once_with(
        query="academia churrasqueira",
        neighborhood="Boa Vista",
        min_price=None,
        max_price=Decimal("700000"),
        min_bedrooms=3,
        min_bathrooms=None,
        min_parking_spaces=None,
        min_usable_area=70,
        available=True,
        limit=5,
    )


def test_search_uses_default_query_when_no_preferences_exist():
    hybrid_search_service = Mock()

    hybrid_search_service.search.return_value = []

    service = ConversationPropertySearchService(
        hybrid_search_service=hybrid_search_service,
    )

    state = ConversationState(
        conversation_id="search-002",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
    )

    result = service.search(state)

    assert result == []

    hybrid_search_service.search.assert_called_once_with(
        query="imóvel residencial",
        neighborhood="Boa Vista",
        min_price=None,
        max_price=Decimal("700000"),
        min_bedrooms=3,
        min_bathrooms=None,
        min_parking_spaces=None,
        min_usable_area=None,
        available=True,
        limit=5,
    )