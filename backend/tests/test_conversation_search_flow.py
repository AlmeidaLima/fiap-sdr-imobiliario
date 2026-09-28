from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from app.schemas.conversation import ConversationState
from app.services.conversation_service import ConversationService


def test_does_not_search_properties_when_conversation_is_not_qualified():
    property_search_service = Mock()

    service = ConversationService(
        property_search_service=property_search_service,
    )

    state = ConversationState(
        conversation_id="search-flow-001",
    )

    result = service.process_turn(
        state,
        "Quero um apartamento no Boa Vista",
    )

    assert result.qualification.qualified is False
    assert result.properties == []

    property_search_service.search.assert_not_called()


def test_searches_properties_when_conversation_becomes_qualified():
    property_search_service = Mock()

    property_search_service.search.return_value = []

    service = ConversationService(
        property_search_service=property_search_service,
    )

    state = ConversationState(
        conversation_id="search-flow-002",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
    )

    result = service.process_turn(
        state,
        "Quero pelo menos 3 quartos",
    )

    assert result.qualification.qualified is True
    assert result.qualification.missing_fields == []
    assert result.qualification.next_question is None
    assert result.properties == []

    property_search_service.search.assert_called_once()

    searched_state = (
        property_search_service
        .search
        .call_args
        .args[0]
    )

    assert searched_state.neighborhood == "Boa Vista"
    assert searched_state.max_price == Decimal("700000")
    assert searched_state.min_bedrooms == 3


def test_search_records_presented_property_ids_in_conversation_state():
    property_search_service = Mock()
    first_property = SimpleNamespace(property=SimpleNamespace(id=20))
    second_property = SimpleNamespace(property=SimpleNamespace(id=10))
    property_search_service.search.return_value = [
        (first_property, 0.95),
        (second_property, 0.90),
        (first_property, 0.85),
    ]
    service = ConversationService(
        property_search_service=property_search_service,
    )
    state = ConversationState(
        conversation_id="search-flow-003",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
    )

    result = service.process_turn(state, "Prefiro churrasqueira")

    assert result.state.presented_property_ids == [20, 10]
