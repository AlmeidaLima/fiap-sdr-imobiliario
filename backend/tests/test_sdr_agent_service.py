from unittest.mock import Mock

from app.schemas.conversation import ConversationState
from app.services.sdr_agent_service import SDRAgentService


def test_sdr_agent_service_processes_unqualified_turn():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    service = SDRAgentService(
        property_search_service_factory=property_search_service_factory,
    )

    state = ConversationState(
        conversation_id="sdr-service-001",
    )

    result = service.process_turn(
        conversation_state=state,
        message="Quero um apartamento no Boa Vista",
    )

    assert result.state.neighborhood == "Boa Vista"
    assert result.qualification.qualified is False
    assert result.qualification.next_question is not None
    assert result.properties == []

    property_search_service.search.assert_not_called()
    property_search_service_factory.assert_not_called()


def test_sdr_agent_service_searches_when_qualified():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    expected_properties = [
        ("property-1", 0.95),
        ("property-2", 0.90),
    ]

    property_search_service.search.return_value = expected_properties

    service = SDRAgentService(
        property_search_service_factory=property_search_service_factory,
    )

    state = ConversationState(
        conversation_id="sdr-service-002",
    )

    result = service.process_turn(
        conversation_state=state,
        message=(
            "Quero um apartamento no Boa Vista "
            "com 3 quartos até 700 mil"
        ),
    )

    assert result.state.neighborhood == "Boa Vista"
    assert result.state.min_bedrooms == 3
    assert result.state.max_price == 700000

    assert result.qualification.qualified is True
    assert result.properties == expected_properties

    property_search_service.search.assert_called_once()
    property_search_service_factory.assert_called_once()