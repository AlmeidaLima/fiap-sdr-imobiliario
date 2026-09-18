from decimal import Decimal

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