from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from app.schemas.conversation import ConversationState
from app.services.sdr_agent_service import SDRAgentService


class FakeLLMService:
    histories = []

    def generate_response(self, **kwargs):
        self.histories.append(kwargs["conversation_history"])
        return "Resposta natural"


def create_property_results():
    property_model = SimpleNamespace(
        id=1, external_id="property-1", title="Apartamento teste",
        description=None, neighborhood="Boa Vista", usable_area=80,
        bedrooms=3, bathrooms=2, parking_spaces=1,
        price=Decimal("650000.00"),
    )
    return [(SimpleNamespace(property=property_model), 0.95)]


def test_sdr_agent_service_processes_unqualified_turn():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    service = SDRAgentService(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=FakeLLMService,
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
    assert result.response == "Resposta natural"

    property_search_service.search.assert_not_called()
    property_search_service_factory.assert_not_called()


def test_sdr_agent_service_searches_when_qualified():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    expected_properties = create_property_results()

    property_search_service.search.return_value = expected_properties

    service = SDRAgentService(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=FakeLLMService,
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
    assert result.response == "Resposta natural"

    property_search_service.search.assert_called_once()
    property_search_service_factory.assert_called_once()


def test_sdr_agent_service_limits_history_to_six_records():
    FakeLLMService.histories = []
    service = SDRAgentService(
        property_search_service_factory=Mock(),
        llm_service_factory=FakeLLMService,
    )
    history = [
        {"role": "user", "content": f"mensagem {index}"}
        for index in range(8)
    ]

    service.process_turn(
        conversation_state=ConversationState(
            conversation_id="sdr-service-003",
        ),
        message="Quero um apartamento.",
        conversation_history=history,
    )

    assert len(FakeLLMService.histories[-1]) == 6
    assert FakeLLMService.histories[-1][0]["content"] == "mensagem 2"
