from decimal import Decimal

from app.schemas.conversation import ConversationState
from app.services.conversation_service import ConversationService


def test_conversation_turn_guides_customer_until_qualified():
    service = ConversationService()

    state = ConversationState(
        conversation_id="turn-001",
    )

    # Turno 1
    result = service.process_turn(
        state,
        "Quero um apartamento no Boa Vista",
    )

    state = result.state

    assert state.neighborhood == "Boa Vista"
    assert result.qualification.qualified is False

    assert result.qualification.missing_fields == [
        "max_price",
        "min_bedrooms",
    ]

    assert (
            result.qualification.next_question
            == "Qual é o valor máximo que você pretende investir no imóvel?"
    )

    # Turno 2
    result = service.process_turn(
        state,
        "Até 700 mil",
    )

    state = result.state

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")

    assert result.qualification.qualified is False

    assert result.qualification.missing_fields == [
        "min_bedrooms",
    ]

    assert (
            result.qualification.next_question
            == "Quantos quartos você procura?"
    )

    # Turno 3
    result = service.process_turn(
        state,
        "Quero pelo menos 3 quartos",
    )

    state = result.state

    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")
    assert state.min_bedrooms == 3

    assert result.qualification.qualified is True
    assert result.qualification.missing_fields == []
    assert result.qualification.next_question is None