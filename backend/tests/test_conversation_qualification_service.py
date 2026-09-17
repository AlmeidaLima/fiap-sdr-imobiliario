from decimal import Decimal

from app.schemas.conversation import ConversationState
from app.services.conversation_qualification_service import (
    ConversationQualificationService,
)


def test_qualification_identifies_all_missing_fields():
    service = ConversationQualificationService()

    state = ConversationState(
        conversation_id="qualification-001",
    )

    result = service.qualify(state)

    assert result.qualified is False

    assert result.missing_fields == [
        "neighborhood",
        "max_price",
        "min_bedrooms",
    ]

    assert (
            result.next_question
            == "Em qual bairro ou região você procura o imóvel?"
    )


def test_qualification_asks_for_max_price():
    service = ConversationQualificationService()

    state = ConversationState(
        conversation_id="qualification-002",
        neighborhood="Boa Vista",
    )

    result = service.qualify(state)

    assert result.qualified is False

    assert result.missing_fields == [
        "max_price",
        "min_bedrooms",
    ]

    assert (
            result.next_question
            == "Qual é o valor máximo que você pretende investir no imóvel?"
    )


def test_qualification_asks_for_bedrooms():
    service = ConversationQualificationService()

    state = ConversationState(
        conversation_id="qualification-003",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
    )

    result = service.qualify(state)

    assert result.qualified is False

    assert result.missing_fields == [
        "min_bedrooms",
    ]

    assert (
            result.next_question
            == "Quantos quartos você procura?"
    )


def test_qualification_marks_complete_state_as_qualified():
    service = ConversationQualificationService()

    state = ConversationState(
        conversation_id="qualification-004",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
    )

    result = service.qualify(state)

    assert result.qualified is True
    assert result.missing_fields == []
    assert result.next_question is None