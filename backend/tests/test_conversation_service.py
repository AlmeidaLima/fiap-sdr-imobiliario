from decimal import Decimal

import pytest

from app.schemas.conversation import ConversationState
from app.schemas.property_search_intent import PropertySearchIntent
from app.services.conversation_service import ConversationService


def test_merge_intent_adds_new_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-001",
    )

    intent = PropertySearchIntent(
        semantic_query="Quero apartamento no Boa Vista",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
    )

    updated_state = service.merge_intent(
        state=state,
        intent=intent,
    )

    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("700000")
    assert updated_state.min_bedrooms == 3


def test_merge_intent_preserves_previous_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-001",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
    )

    intent = PropertySearchIntent(
        semantic_query="Quero 3 quartos",
        min_bedrooms=3,
    )

    updated_state = service.merge_intent(
        state=state,
        intent=intent,
    )

    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("700000")
    assert updated_state.min_bedrooms == 3


def test_merge_intent_overwrites_changed_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-001",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
    )

    intent = PropertySearchIntent(
        semantic_query="Na verdade pode ser até 800 mil",
        max_price=Decimal("800000"),
    )

    updated_state = service.merge_intent(
        state=state,
        intent=intent,
    )

    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("800000")


def test_merge_intent_accumulates_semantic_preferences():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-001",
        semantic_preferences=[
            "Quero um imóvel com academia",
        ],
    )

    intent = PropertySearchIntent(
        semantic_query="Também quero churrasqueira",
    )

    updated_state = service.merge_intent(
        state=state,
        intent=intent,
    )

    assert updated_state.semantic_preferences == [
        "Quero um imóvel com academia",
        "Também quero churrasqueira",
    ]


def test_merge_intent_does_not_duplicate_semantic_preference():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-001",
        semantic_preferences=[
            "Quero um imóvel com academia",
        ],
    )

    intent = PropertySearchIntent(
        semantic_query="Quero um imóvel com academia",
    )

    updated_state = service.merge_intent(
        state=state,
        intent=intent,
    )

    assert updated_state.semantic_preferences == [
        "Quero um imóvel com academia",
    ]


def test_process_message_extracts_lead_name():
    service = ConversationService()

    state = ConversationState(
        conversation_id="test-lead-name",
    )

    updated_state = service.process_message(
        state=state,
        message="Meu nome é Rafael Almeida",
    )

    assert updated_state.lead_name == "Rafael Almeida"


def test_process_message_preserves_lead_name():
    service = ConversationService()

    state = ConversationState(
        conversation_id="test-lead-name",
        lead_name="Rafael Almeida",
    )

    updated_state = service.process_message(
        state=state,
        message="Quero um apartamento no Boa Vista",
    )

    assert updated_state.lead_name == "Rafael Almeida"
    assert updated_state.neighborhood == "Boa Vista"


def test_process_message_adds_commercial_qualification_without_losing_search_data():
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-qualification-001",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
    )

    updated_state = service.process_message(
        state=state,
        message="Quero comprar nos próximos 30 dias",
    )

    assert updated_state.commercial_intent == "COMPRA"
    assert updated_state.urgency_days == 30
    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("700000")


def test_process_message_preserves_commercial_data_between_turns():
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-qualification-002",
        commercial_intent="INVESTIMENTO",
        urgency_days=60,
    )

    updated_state = service.process_message(
        state=state,
        message="Também quero churrasqueira",
    )

    assert updated_state.commercial_intent == "INVESTIMENTO"
    assert updated_state.urgency_days == 60


def test_process_message_clears_legacy_acceptance_without_appointment():
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-qualification-003",
        accepted_meeting_or_visit=True,
    )

    updated_state = service.process_message(
        state=state,
        message="Como funciona a visita?",
    )

    assert updated_state.accepted_meeting_or_visit is False


def test_process_message_preserves_acceptance_backed_by_appointment():
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-qualification-with-appointment",
        appointment_id=123,
        accepted_meeting_or_visit=True,
    )

    updated_state = service.process_message(
        state=state,
        message="Como funciona a visita?",
    )

    assert updated_state.appointment_id == 123
    assert updated_state.accepted_meeting_or_visit is True


@pytest.mark.parametrize(
    "message",
    [
        "Quero visitar",
        "Quero marcar uma visita",
        "Podemos agendar uma visita",
        "Aceito uma visita",
        "Não quero visitar",
        "Como funciona a visita?",
    ],
)
def test_process_message_does_not_activate_acceptance_from_text(message):
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-acceptance-requires-appointment",
    )

    updated_state = service.process_message(state=state, message=message)

    assert updated_state.accepted_meeting_or_visit is False


def test_process_message_does_not_replace_urgency_with_zero():
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-qualification-004",
        urgency_days=60,
    )

    updated_state = service.process_message(
        state=state,
        message="Em 0 dias",
    )

    assert updated_state.urgency_days == 60


@pytest.mark.parametrize(
    "message",
    [
        "Não quero comprar",
        "Não quero alugar",
        "Não quero investir",
        "Não quero visitar",
        "Não quero marcar uma reunião",
        "Como funciona a compra?",
        "Como funciona o aluguel?",
        "Como funciona a visita?",
    ],
)
def test_process_message_preserves_commercial_data_for_non_evidence(message):
    service = ConversationService()
    state = ConversationState(
        conversation_id="commercial-qualification-005",
        commercial_intent="COMPRA",
        urgency_days=30,
        appointment_id=123,
        accepted_meeting_or_visit=True,
    )

    updated_state = service.process_message(
        state=state,
        message=message,
    )

    assert updated_state.commercial_intent == "COMPRA"
    assert updated_state.urgency_days == 30
    assert updated_state.accepted_meeting_or_visit is True


def test_process_message_extracts_name_and_commercial_intent_together():
    service = ConversationService()
    state = ConversationState(
        conversation_id="combined-lead-identification",
    )

    updated_state = service.process_message(
        state=state,
        message=(
            "Olá, meu nome é Rafael e estou procurando "
            "um apartamento para comprar."
        ),
    )

    assert updated_state.lead_name == "Rafael"
    assert updated_state.commercial_intent == "COMPRA"
