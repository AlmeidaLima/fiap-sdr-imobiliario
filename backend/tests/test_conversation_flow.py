from decimal import Decimal

from app.schemas.conversation import ConversationState
from app.services.conversation_service import ConversationService


def test_conversation_accumulates_information_across_messages():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-flow-001",
    )

    state = service.process_message(
        state,
        "Quero um apartamento no Boa Vista",
    )

    assert state.neighborhood == "Boa Vista"

    state = service.process_message(
        state,
        "Até 700 mil",
    )

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")

    state = service.process_message(
        state,
        "Quero pelo menos 3 quartos",
    )

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")
    assert state.min_bedrooms == 3

    state = service.process_message(
        state,
        "Pelo menos 70 m²",
    )

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")
    assert state.min_bedrooms == 3
    assert state.min_usable_area == 70


def test_conversation_updates_changed_information():
    service = ConversationService()

    state = ConversationState(
        conversation_id="conversation-flow-002",
    )

    state = service.process_message(
        state,
        "Quero apartamento no Boa Vista até 700 mil",
    )

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")

    state = service.process_message(
        state,
        "Na verdade pode ser até 800 mil",
    )

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("800000")