from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from app.agents.nodes import process_message_node
from app.schemas.conversation import ConversationQualification, ConversationState
from app.services.llm_client import LLMClientError


def create_property_result():
    property_model = SimpleNamespace(
        id=1, external_id="property-1", title="Apartamento teste",
        description="Imóvel com área de lazer", neighborhood="Boa Vista",
        usable_area=80, bedrooms=3, bathrooms=2, parking_spaces=1,
        price=Decimal("650000.00"),
    )
    return (SimpleNamespace(property=property_model), 0.95)


def test_process_message_node_updates_conversation_state():
    state = {
        "conversation_id": "agent-test-001",
        "message": "Quero um apartamento no Boa Vista",
        "conversation_state": ConversationState(
            conversation_id="agent-test-001",
        ),
    }

    result = process_message_node(state)

    assert "conversation_state" in result

    conversation_state = result["conversation_state"]

    assert conversation_state.conversation_id == "agent-test-001"
    assert conversation_state.neighborhood == "Boa Vista"


def test_process_message_node_creates_conversation_state_when_missing():
    state = {
        "conversation_id": "agent-test-002",
        "message": "Até 700 mil",
    }

    result = process_message_node(state)

    conversation_state = result["conversation_state"]

    assert conversation_state.conversation_id == "agent-test-002"
    assert conversation_state.max_price == 700000

def test_qualify_conversation_node_returns_not_qualified():
    from app.agents.nodes import qualify_conversation_node

    state = {
        "conversation_state": ConversationState(
            conversation_id="agent-test-003",
            neighborhood="Boa Vista",
        ),
    }

    result = qualify_conversation_node(state)

    qualification = result["qualification"]

    assert qualification.qualified is False
    assert "max_price" in qualification.missing_fields
    assert "min_bedrooms" in qualification.missing_fields
    assert qualification.next_question is not None


def test_qualify_conversation_node_returns_qualified():
    from app.agents.nodes import qualify_conversation_node

    state = {
        "conversation_state": ConversationState(
            conversation_id="agent-test-004",
            neighborhood="Boa Vista",
            max_price=700000,
            min_bedrooms=3,
        ),
    }

    result = qualify_conversation_node(state)

    qualification = result["qualification"]

    assert qualification.qualified is True
    assert qualification.missing_fields == []
    assert qualification.next_question is None

def test_ask_question_node_returns_next_question():
    from app.agents.nodes import ask_question_node
    from app.schemas.conversation import ConversationQualification

    question = (
        "Qual é o valor máximo que você pretende "
        "investir no imóvel?"
    )

    state = {
        "qualification": ConversationQualification(
            qualified=False,
            missing_fields=["max_price", "min_bedrooms"],
            next_question=question,
        )
    }

    result = ask_question_node(state)

    assert result["response"] == question


def test_ask_question_node_returns_none_when_there_is_no_next_question():
    from app.agents.nodes import ask_question_node
    from app.schemas.conversation import ConversationQualification

    state = {
        "qualification": ConversationQualification(
            qualified=True,
            missing_fields=[],
            next_question=None,
        )
    }

    result = ask_question_node(state)

    assert result["response"] is None

def test_search_properties_node_uses_property_search_service():
    from app.agents.nodes import search_properties_node

    conversation_state = ConversationState(
        conversation_id="agent-test-005",
        neighborhood="Boa Vista",
        max_price=700000,
        min_bedrooms=3,
    )

    expected_properties = [
        ("property-1", 0.95),
        ("property-2", 0.90),
    ]

    property_search_service = Mock()
    property_search_service.search.return_value = expected_properties

    state = {
        "conversation_state": conversation_state,
    }

    result = search_properties_node(
        state,
        property_search_service,
    )

    assert result["properties"] == expected_properties

    property_search_service.search.assert_called_once_with(
        conversation_state,
        limit=5,
    )


def test_generate_response_node_uses_controlled_context():
    from app.agents.nodes import generate_response_node

    llm_service = Mock()
    llm_service.generate_response.return_value = "Encontrei uma opção."
    result = generate_response_node(
        {
            "message": "Quais imóveis você encontrou?",
            "conversation_state": ConversationState(
                conversation_id="agent-test-006", neighborhood="Boa Vista",
                max_price=700000, min_bedrooms=3,
            ),
            "qualification": ConversationQualification(
                qualified=True, missing_fields=[],
            ),
            "conversation_history": [{"role": "user", "content": "Olá"}],
            "properties": [create_property_result()],
        },
        llm_service,
    )

    assert result["response"] == "Encontrei uma opção."
    context = llm_service.generate_response.call_args.kwargs["properties_context"]
    assert context[0]["id"] == 1
    assert context[0]["price"] == "650000.00"


def test_generate_response_node_falls_back_to_deterministic_question():
    from app.agents.nodes import generate_response_node

    llm_service = Mock()
    llm_service.generate_response.side_effect = LLMClientError("indisponível")
    question = "Qual é o valor máximo que você pretende investir?"
    result = generate_response_node(
        {
            "message": "Quero um apartamento.",
            "conversation_state": ConversationState(
                conversation_id="agent-test-007",
            ),
            "qualification": ConversationQualification(
                qualified=False, missing_fields=["max_price"],
                next_question=question,
            ),
        },
        llm_service,
    )

    assert result["response"] == question


def test_generate_response_node_falls_back_when_search_has_no_results():
    from app.agents.nodes import generate_response_node

    llm_service = Mock()
    llm_service.generate_response.side_effect = LLMClientError("indisponível")
    result = generate_response_node(
        {
            "message": "Quais opções existem?",
            "conversation_state": ConversationState(
                conversation_id="agent-test-008",
            ),
            "qualification": ConversationQualification(
                qualified=True, missing_fields=[],
            ),
            "properties": [],
        },
        llm_service,
    )

    assert "Não encontrei imóveis compatíveis" in result["response"]
