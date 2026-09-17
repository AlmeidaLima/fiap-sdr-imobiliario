from decimal import Decimal

from app.schemas.conversation import ConversationState
from app.schemas.property_search_intent import PropertySearchIntent
from app.services.conversation_service import ConversationService


def test_merge_intent_adds_new_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-001",
        neighborhood="Boa Vista",
    )

    intent = PropertySearchIntent(
        max_price=Decimal("700000"),
        min_bedrooms=3,
        semantic_query="até 700 mil com 3 quartos",
    )

    updated_state = service.merge_intent(
        state,
        intent,
    )

    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("700000")
    assert updated_state.min_bedrooms == 3


def test_merge_intent_preserves_previous_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-002",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
    )

    intent = PropertySearchIntent(
        min_usable_area=70,
        semantic_query="pelo menos 70 m²",
    )

    updated_state = service.merge_intent(
        state,
        intent,
    )

    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("700000")
    assert updated_state.min_bedrooms == 3
    assert updated_state.min_usable_area == 70


def test_merge_intent_overwrites_changed_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-003",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
    )

    intent = PropertySearchIntent(
        max_price=Decimal("800000"),
        semantic_query="na verdade pode ser até 800 mil",
    )

    updated_state = service.merge_intent(
        state,
        intent,
    )

    assert updated_state.neighborhood == "Boa Vista"
    assert updated_state.max_price == Decimal("800000")


def test_merge_intent_accumulates_semantic_preferences():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-004",
        semantic_preferences=[
            "academia",
        ],
    )

    intent = PropertySearchIntent(
        semantic_query="churrasqueira",
    )

    updated_state = service.merge_intent(
        state,
        intent,
    )

    assert updated_state.semantic_preferences == [
        "academia",
        "churrasqueira",
    ]


def test_merge_intent_does_not_duplicate_semantic_preference():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-005",
        semantic_preferences=[
            "academia",
        ],
    )

    intent = PropertySearchIntent(
        semantic_query="academia",
    )

    updated_state = service.merge_intent(
        state,
        intent,
    )

    assert updated_state.semantic_preferences == [
        "academia",
    ]