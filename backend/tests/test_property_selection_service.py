import pytest

from app.core.exceptions import ApplicationException
from app.schemas.conversation import ConversationState
from app.services.property_selection_service import PropertySelectionService


def test_selects_presented_property_by_internal_id():
    state = ConversationState(
        conversation_id='selection-001',
        presented_property_ids=[10, 20],
    )

    result = PropertySelectionService().select_property(state, 20)

    assert result.selected_property_id == 20
    assert result.appointment_stage == "SELECTED"
    assert result.accepted_meeting_or_visit is False
    assert result.lead_score == 0
    assert state.selected_property_id is None


def test_rejects_property_that_was_not_presented():
    state = ConversationState(
        conversation_id='selection-002',
        presented_property_ids=[10],
    )

    with pytest.raises(ApplicationException) as exc_info:
        PropertySelectionService().select_property(state, 999)

    assert exc_info.value.error == 'invalid_property_selection'
    assert state.selected_property_id is None


def test_invalid_selection_preserves_previous_valid_selection():
    state = ConversationState(
        conversation_id='selection-003',
        presented_property_ids=[10, 20],
        selected_property_id=10,
    )

    with pytest.raises(ApplicationException):
        PropertySelectionService().select_property(state, 999)

    assert state.selected_property_id == 10


def test_selecting_same_property_is_idempotent():
    state = ConversationState(
        conversation_id='selection-004',
        presented_property_ids=[10],
        selected_property_id=10,
        appointment_stage="AWAITING_DATE",
        appointment_type="VISITA",
    )

    result = PropertySelectionService().select_property(state, 10)

    assert result.selected_property_id == 10
    assert result.presented_property_ids == [10]
    assert result.appointment_stage == "AWAITING_DATE"
    assert result.appointment_type == "VISITA"


def test_selection_does_not_accept_external_id():
    state = ConversationState(
        conversation_id='selection-005',
        presented_property_ids=[10],
    )

    with pytest.raises(ApplicationException):
        PropertySelectionService().select_property(state, 123456)
