import io
import logging
from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from app.agents.nodes import process_message_node
from app.schemas.conversation import ConversationQualification, ConversationState
from app.services.llm_client import LLMClientError
from app.core.observability import (
    SafeKeyValueFormatter,
    reset_request_id,
    set_request_id,
)


@contextmanager
def capture_application_logs(request_id="request-agent-001"):
    logger = logging.getLogger("app")
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SafeKeyValueFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    token = set_request_id(request_id)
    try:
        yield stream
    finally:
        reset_request_id(token)
        logger.handlers = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate


def create_property_result(property_id=1):
    property_model = SimpleNamespace(
        id=property_id, external_id=f"property-{property_id}", title="Apartamento teste",
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


def test_calculate_lead_score_node_empty_state_is_cold():
    from app.agents.nodes import calculate_lead_score_node

    original_state = ConversationState(
        conversation_id="agent-score-001",
    )

    result = calculate_lead_score_node(
        {"conversation_state": original_state}
    )
    updated_state = result["conversation_state"]

    assert updated_state.lead_score == 0
    assert updated_state.lead_classification == "FRIO"


def test_calculate_lead_score_node_updates_copy_and_preserves_fields():
    from app.agents.nodes import calculate_lead_score_node

    original_state = ConversationState(
        conversation_id="agent-score-002",
        lead_name="Rafael Teste",
        commercial_intent="COMPRA",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
        urgency_days=30,
        accepted_meeting_or_visit=True,
        semantic_preferences=["academia"],
    )

    result = calculate_lead_score_node(
        {"conversation_state": original_state}
    )
    updated_state = result["conversation_state"]

    assert updated_state.lead_score == 100
    assert updated_state.lead_classification == "QUENTE"
    assert updated_state.lead_name == "Rafael Teste"
    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("700000")
    assert updated_state.min_bedrooms == 3
    assert updated_state.semantic_preferences == ["academia"]
    assert original_state.lead_score == 0
    assert original_state.lead_classification == "FRIO"

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

    expected_properties = [create_property_result()]

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
    assert result["conversation_state"].presented_property_ids == [1]

    property_search_service.search.assert_called_once_with(
        conversation_state,
        limit=5,
    )


def test_search_properties_node_deduplicates_presented_property_ids():
    from app.agents.nodes import search_properties_node

    conversation_state = ConversationState(
        conversation_id='agent-search-deduplicate',
    )
    property_search_service = Mock()
    property_search_service.search.return_value = [
        create_property_result(),
        create_property_result(),
    ]

    result = search_properties_node(
        {'conversation_state': conversation_state},
        property_search_service,
    )

    assert result['conversation_state'].presented_property_ids == [1]


def test_search_without_results_clears_presented_properties_and_selection():
    from app.agents.nodes import search_properties_node

    conversation_state = ConversationState(
        conversation_id='agent-search-empty',
        presented_property_ids=[1],
        selected_property_id=1,
    )
    property_search_service = Mock()
    property_search_service.search.return_value = []

    result = search_properties_node(
        {'conversation_state': conversation_state},
        property_search_service,
    )

    updated_state = result['conversation_state']
    assert updated_state.presented_property_ids == []
    assert updated_state.selected_property_id is None
    assert updated_state.appointment_stage == "NONE"


def test_new_search_preserves_selection_still_presented():
    from app.agents.nodes import search_properties_node

    conversation_state = ConversationState(
        conversation_id='agent-search-preserve-selection',
        presented_property_ids=[1, 2],
        selected_property_id=1,
    )
    property_search_service = Mock()
    property_search_service.search.return_value = [create_property_result()]

    result = search_properties_node(
        {'conversation_state': conversation_state},
        property_search_service,
    )

    updated_state = result['conversation_state']
    assert updated_state.presented_property_ids == [1]
    assert updated_state.selected_property_id == 1


def test_new_search_clears_selection_no_longer_presented():
    from app.agents.nodes import search_properties_node

    conversation_state = ConversationState(
        conversation_id='agent-search-clear-selection',
        presented_property_ids=[1],
        selected_property_id=1,
    )
    property_search_service = Mock()
    property_search_service.search.return_value = [
        create_property_result(property_id=2),
    ]

    result = search_properties_node(
        {'conversation_state': conversation_state},
        property_search_service,
    )

    updated_state = result['conversation_state']
    assert updated_state.presented_property_ids == [2]
    assert updated_state.selected_property_id is None
    assert updated_state.appointment_stage == "NONE"


def test_turn_without_search_preserves_presented_properties():
    state = {
        'conversation_id': 'agent-no-search',
        'message': 'Meu nome e Rafael',
        'conversation_state': ConversationState(
            conversation_id='agent-no-search',
            presented_property_ids=[1, 2],
            selected_property_id=1,
        ),
    }

    result = process_message_node(state)

    updated_state = result['conversation_state']
    assert updated_state.presented_property_ids == [1, 2]
    assert updated_state.selected_property_id == 1


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


def test_llm_success_log_contains_request_id_without_content():
    from app.agents.nodes import generate_response_node

    llm_service = Mock()
    llm_service.generate_response.return_value = "RESPOSTA_SENSIVEL_LLM"
    state = {
        "conversation_id": "agent-log-success",
        "message": "MENSAGEM_SENSIVEL_USUARIO",
        "conversation_state": ConversationState(
            conversation_id="agent-log-success",
        ),
        "qualification": ConversationQualification(
            qualified=False,
            missing_fields=["max_price"],
            next_question="Pergunta seguinte",
        ),
    }

    with capture_application_logs() as output:
        result = generate_response_node(state, llm_service)

    assert result["response"] == "RESPOSTA_SENSIVEL_LLM"
    assert "event=llm_call_completed" in output.getvalue()
    assert "request_id=request-agent-001" in output.getvalue()
    assert "conversation_id=agent-log-success" in output.getvalue()
    assert "MENSAGEM_SENSIVEL_USUARIO" not in output.getvalue()
    assert "RESPOSTA_SENSIVEL_LLM" not in output.getvalue()


def test_llm_fallback_log_is_safe_and_contains_request_id():
    from app.agents.nodes import generate_response_node

    llm_service = Mock()
    llm_service.generate_response.side_effect = LLMClientError(
        "SEGREDO_TESTE_LLM"
    )
    state = {
        "conversation_id": "agent-log-fallback",
        "message": "MENSAGEM_SENSIVEL_USUARIO",
        "conversation_state": ConversationState(
            conversation_id="agent-log-fallback",
        ),
        "qualification": ConversationQualification(
            qualified=False,
            missing_fields=["max_price"],
            next_question="Pergunta determinística",
        ),
    }

    with capture_application_logs() as output:
        result = generate_response_node(state, llm_service)

    assert result["response"] == "Pergunta determinística"
    assert "event=llm_fallback_activated" in output.getvalue()
    assert "request_id=request-agent-001" in output.getvalue()
    assert "error_type=LLMClientError" in output.getvalue()
    assert "SEGREDO_TESTE_LLM" not in output.getvalue()
    assert "MENSAGEM_SENSIVEL_USUARIO" not in output.getvalue()


def test_property_search_logs_count_duration_and_request_id():
    from app.agents.nodes import search_properties_node

    search_service = Mock()
    search_service.search.return_value = [create_property_result()]
    state = {
        "conversation_id": "agent-search-log",
        "conversation_state": ConversationState(
            conversation_id="agent-search-log",
        ),
        "limit": 5,
    }

    with capture_application_logs() as output:
        result = search_properties_node(state, search_service)

    assert len(result["properties"]) == 1
    assert "event=property_search_started" in output.getvalue()
    assert "event=property_search_completed" in output.getvalue()
    assert "request_id=request-agent-001" in output.getvalue()
    assert "property_count=1" in output.getvalue()
    assert "duration_ms=" in output.getvalue()


def test_property_search_failure_log_does_not_include_exception_text():
    from app.agents.nodes import search_properties_node

    search_service = Mock()
    search_service.search.side_effect = RuntimeError(
        "SEGREDO_TESTE_BUSCA"
    )
    state = {
        "conversation_id": "agent-search-failure",
        "conversation_state": ConversationState(
            conversation_id="agent-search-failure",
        ),
    }

    with capture_application_logs() as output:
        try:
            search_properties_node(state, search_service)
        except RuntimeError:
            pass

    assert "event=property_search_failed" in output.getvalue()
    assert "error_type=RuntimeError" in output.getvalue()
    assert "request_id=request-agent-001" in output.getvalue()
    assert "SEGREDO_TESTE_BUSCA" not in output.getvalue()
