from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from app.agents.sdr_graph import build_sdr_graph


class FakeLLMService:
    def generate_response(self, **kwargs):
        return "Resposta natural"


def create_property_results():
    property_model = SimpleNamespace(
        id=1, external_id="property-1", title="Apartamento teste",
        description=None, neighborhood="Boa Vista", usable_area=80,
        bedrooms=3, bathrooms=2, parking_spaces=1,
        price=Decimal("650000.00"),
    )
    return [(SimpleNamespace(property=property_model), 0.95)]


def test_sdr_graph_asks_for_missing_information():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    graph = build_sdr_graph(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=FakeLLMService,
    )

    result = graph.invoke(
        {
            "conversation_id": "graph-test-001",
            "message": "Quero um apartamento no Boa Vista",
        }
    )

    assert result["conversation_state"].neighborhood == "Boa Vista"
    assert result["conversation_state"].lead_score == 10
    assert result["conversation_state"].lead_classification == "FRIO"

    assert result["qualification"].qualified is False

    assert result["qualification"].next_question is not None

    assert result["response"] == "Resposta natural"

    property_search_service.search.assert_not_called()

    property_search_service_factory.assert_not_called()


def test_sdr_graph_searches_properties_when_qualified():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    expected_properties = create_property_results()

    property_search_service.search.return_value = expected_properties

    graph = build_sdr_graph(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=FakeLLMService,
    )

    result = graph.invoke(
        {
            "conversation_id": "graph-test-002",
            "message": (
                "Quero um apartamento no Boa Vista "
                "com 3 quartos até 700 mil"
            ),
        }
    )

    assert result["conversation_state"].neighborhood == "Boa Vista"
    assert result["conversation_state"].min_bedrooms == 3
    assert result["conversation_state"].max_price == 700000
    assert result["conversation_state"].lead_score == 30
    assert result["conversation_state"].lead_classification == "FRIO"

    assert result["qualification"].qualified is True

    assert result["properties"] == expected_properties

    property_search_service.search.assert_called_once()

    property_search_service_factory.assert_called_once()


def test_sdr_graph_preserves_state_across_multiple_turns():
    property_search_service = Mock()

    property_search_service_factory = Mock(
        return_value=property_search_service,
    )

    expected_properties = create_property_results()

    property_search_service.search.return_value = expected_properties

    graph = build_sdr_graph(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=FakeLLMService,
    )

    # Turno 1 — informa o bairro
    first_turn = graph.invoke(
        {
            "conversation_id": "graph-multiturn-001",
            "message": "Quero comprar um apartamento no Boa Vista",
        }
    )

    assert first_turn["conversation_state"].neighborhood == "Boa Vista"
    assert first_turn["conversation_state"].commercial_intent == "COMPRA"
    assert first_turn["conversation_state"].lead_score == 30
    assert first_turn["conversation_state"].lead_classification == "FRIO"
    assert first_turn["qualification"].qualified is False
    assert first_turn["response"] is not None

    property_search_service.search.assert_not_called()
    property_search_service_factory.assert_not_called()

    # Turno 2 — informa o orçamento
    second_turn = graph.invoke(
        {
            "conversation_id": "graph-multiturn-001",
            "message": "Até 700 mil",
            "conversation_state": first_turn["conversation_state"],
        }
    )

    assert second_turn["conversation_state"].neighborhood == "Boa Vista"
    assert second_turn["conversation_state"].max_price == 700000
    assert second_turn["conversation_state"].lead_score == 50
    assert second_turn["conversation_state"].lead_classification == "MORNO"
    assert second_turn["qualification"].qualified is False
    assert second_turn["response"] is not None

    property_search_service.search.assert_not_called()
    property_search_service_factory.assert_not_called()

    # Turno 3 — informa a quantidade de quartos
    third_turn = graph.invoke(
        {
            "conversation_id": "graph-multiturn-001",
            "message": "Preciso em 30 dias e quero 3 quartos",
            "conversation_state": second_turn["conversation_state"],
        }
    )

    assert third_turn["conversation_state"].neighborhood == "Boa Vista"
    assert third_turn["conversation_state"].max_price == 700000
    assert third_turn["conversation_state"].min_bedrooms == 3
    assert third_turn["conversation_state"].urgency_days == 30
    assert third_turn["conversation_state"].lead_score == 75
    assert third_turn["conversation_state"].lead_classification == "QUENTE"

    assert third_turn["qualification"].qualified is True

    assert third_turn["properties"] == expected_properties

    property_search_service.search.assert_called_once()
    property_search_service_factory.assert_called_once()


def test_sdr_graph_processes_name_and_commercial_intent_without_searching():
    property_search_service = Mock()
    property_search_service_factory = Mock(
        return_value=property_search_service,
    )
    graph = build_sdr_graph(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=FakeLLMService,
    )

    result = graph.invoke(
        {
            "conversation_id": "graph-combined-identification",
            "message": (
                "Olá, meu nome é Rafael e estou procurando "
                "um apartamento para comprar."
            ),
        }
    )

    assert result["conversation_state"].lead_name == "Rafael"
    assert result["conversation_state"].commercial_intent == "COMPRA"
    assert result["conversation_state"].lead_score == 20
    assert result["conversation_state"].lead_classification == "FRIO"
    assert result["qualification"].qualified is False
    assert result["qualification"].missing_fields == [
        "neighborhood",
        "max_price",
        "min_bedrooms",
    ]
    property_search_service.search.assert_not_called()
    property_search_service_factory.assert_not_called()
