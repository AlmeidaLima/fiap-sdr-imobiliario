from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.conversation import (
    ConversationState,
)


def test_conversation_state_accepts_valid_data():
    state = ConversationState(
        conversation_id="conversation-001",
        neighborhood="Boa Vista",
        max_price=Decimal("700000"),
        min_bedrooms=3,
        min_usable_area=70,
        semantic_preferences=[
            "academia",
            "churrasqueira",
        ],
    )

    assert state.conversation_id == "conversation-001"
    assert state.neighborhood == "Boa Vista"
    assert state.max_price == Decimal("700000")
    assert state.min_bedrooms == 3
    assert state.min_usable_area == 70

    assert state.semantic_preferences == [
        "academia",
        "churrasqueira",
    ]


def test_conversation_state_starts_with_empty_criteria():
    state = ConversationState(
        conversation_id="conversation-002",
    )

    assert state.neighborhood is None
    assert state.min_price is None
    assert state.max_price is None
    assert state.min_bedrooms is None
    assert state.min_bathrooms is None
    assert state.min_parking_spaces is None
    assert state.min_usable_area is None
    assert state.semantic_preferences == []
    assert state.commercial_intent is None
    assert state.urgency_days is None
    assert state.accepted_meeting_or_visit is False
    assert state.lead_score == 0
    assert state.lead_classification == "FRIO"
    assert state.presented_property_ids == []
    assert state.selected_property_id is None
    assert state.appointment_stage == "NONE"
    assert state.appointment_type is None
    assert state.appointment_date is None
    assert state.appointment_time is None
    assert state.appointment_id is None


def test_conversation_state_accepts_persisted_state_without_property_selection():
    state = ConversationState.model_validate(
        {
            'conversation_id': 'conversation-old',
            'neighborhood': 'Boa Vista',
        }
    )

    assert state.presented_property_ids == []
    assert state.selected_property_id is None
    assert state.appointment_stage == "NONE"


def test_conversation_state_rejects_negative_price():
    with pytest.raises(ValidationError):
        ConversationState(
            conversation_id="conversation-003",
            max_price=Decimal("-1"),
        )
