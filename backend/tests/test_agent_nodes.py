from app.agents.nodes import process_message_node
from app.schemas.conversation import ConversationState


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
    from unittest.mock import Mock

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