from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ApplicationException
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.schemas.conversation import LeadScoreResult
from app.services.appointment_service import AppointmentService


NOW = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)


def confirmed_state(**overrides) -> dict:
    state = {
        "appointment_stage": "CONFIRMED",
        "appointment_type": "VISITA",
        "appointment_date": "2026-09-30",
        "appointment_time": "14:30:00",
        "selected_property_id": 42,
        "commercial_intent": "COMPRA",
        "neighborhood": "Boa Vista",
        "max_price": "400000",
        "lead_score": 50,
        "lead_classification": "MORNO",
        "accepted_meeting_or_visit": False,
    }
    state.update(overrides)
    return state


def build_service(
        conversation: Conversation,
        lead_score_service=None,
):
    appointment_repository = Mock()
    conversation_repository = Mock()
    property_repository = Mock()
    conversation_repository.find_by_conversation_id.return_value = conversation
    property_repository.find_by_id.return_value = object()
    appointment_repository.get_by_idempotency_key.return_value = None

    def save(appointment):
        appointment.id = 7
        return appointment

    appointment_repository.create.side_effect = save
    service = AppointmentService(
        appointment_repository=appointment_repository,
        conversation_repository=conversation_repository,
        property_repository=property_repository,
        business_timezone="America/Sao_Paulo",
        lead_score_service=lead_score_service,
        now_provider=lambda: NOW,
    )
    return service, appointment_repository, conversation_repository


def conversation_with_state(**overrides) -> Conversation:
    return Conversation(
        id=1,
        conversation_id="conversation-1",
        lead_id=3,
        state=confirmed_state(**overrides),
    )


def test_creates_confirmed_visit_from_persisted_state_in_utc():
    conversation = conversation_with_state()
    service, appointment_repository, conversation_repository = build_service(
        conversation
    )

    appointment = service.create_from_conversation("conversation-1")

    assert appointment.lead_id == 3
    assert appointment.property_id == 42
    assert appointment.appointment_type == "VISITA"
    assert appointment.status == "CONFIRMED"
    assert appointment.scheduled_at == datetime(
        2026, 9, 30, 17, 30, tzinfo=timezone.utc
    )
    assert conversation_repository.update_state.call_args.kwargs["state"][
        "appointment_id"
    ] == 7
    persisted = conversation_repository.update_state.call_args.kwargs["state"]
    assert persisted["accepted_meeting_or_visit"] is True
    assert persisted["lead_score"] == 75
    assert persisted["lead_classification"] == "QUENTE"
    appointment_repository.create.assert_called_once()


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"appointment_stage": "AWAITING_CONFIRMATION"}, "appointment_not_confirmed"),
        ({"appointment_type": None}, "missing_appointment_type"),
        ({"appointment_date": None}, "missing_appointment_schedule"),
        ({"appointment_time": None}, "missing_appointment_schedule"),
        ({"selected_property_id": None}, "missing_selected_property"),
    ],
)
def test_rejects_incomplete_or_unconfirmed_state(overrides, error):
    service, _, _ = build_service(conversation_with_state(**overrides))

    with pytest.raises(ApplicationException) as exception:
        service.create_from_conversation("conversation-1")

    assert exception.value.error == error


def test_rejects_conversation_without_lead():
    conversation = conversation_with_state()
    conversation.lead_id = None
    service, _, _ = build_service(conversation)

    with pytest.raises(ApplicationException) as exception:
        service.create_from_conversation("conversation-1")

    assert exception.value.error == "conversation_without_lead"


def test_rejects_nonexistent_property():
    service, _, conversation_repository = build_service(
        conversation_with_state()
    )
    service.property_repository.find_by_id.return_value = None

    with pytest.raises(ApplicationException) as exception:
        service.create_from_conversation("conversation-1")

    assert exception.value.error == "property_not_found"
    conversation_repository.update_state.assert_not_called()


def test_meeting_allows_nullable_property():
    conversation = conversation_with_state(
        appointment_type="REUNIAO",
        selected_property_id=None,
    )
    service, appointment_repository, _ = build_service(conversation)

    appointment = service.create_from_conversation("conversation-1")

    assert appointment.property_id is None
    service.property_repository.find_by_id.assert_not_called()
    appointment_repository.create.assert_called_once()


def test_rejects_past_schedule():
    service, _, _ = build_service(
        conversation_with_state(
            appointment_date="2026-09-27",
        )
    )

    with pytest.raises(ApplicationException) as exception:
        service.create_from_conversation("conversation-1")

    assert exception.value.error == "appointment_in_past"


def test_retry_returns_existing_appointment_without_second_insert():
    conversation = conversation_with_state()
    service, appointment_repository, _ = build_service(conversation)
    existing = Appointment(
        id=9,
        lead_id=3,
        property_id=42,
        appointment_type="VISITA",
        scheduled_at=datetime(2026, 9, 30, 17, 30, tzinfo=timezone.utc),
        status="CONFIRMED",
        idempotency_key="existing",
    )
    appointment_repository.get_by_idempotency_key.return_value = existing

    result = service.create_from_conversation("conversation-1")

    assert result is existing
    appointment_repository.create.assert_not_called()


def test_unique_race_recovers_existing_appointment():
    conversation = conversation_with_state()
    service, appointment_repository, _ = build_service(conversation)
    existing = Appointment(
        id=11,
        lead_id=3,
        property_id=42,
        appointment_type="VISITA",
        scheduled_at=datetime(2026, 9, 30, 17, 30, tzinfo=timezone.utc),
        status="CONFIRMED",
        idempotency_key="existing",
    )
    appointment_repository.get_by_idempotency_key.side_effect = [None, existing]
    appointment_repository.create.side_effect = IntegrityError(
        "insert", {}, Exception("unique")
    )

    result = service.create_from_conversation("conversation-1")

    assert result is existing
    appointment_repository.rollback.assert_called_once()


def test_creation_failure_does_not_apply_commercial_effect():
    conversation = conversation_with_state()
    service, appointment_repository, conversation_repository = build_service(
        conversation
    )
    appointment_repository.create.side_effect = RuntimeError("database error")

    with pytest.raises(RuntimeError, match="database error"):
        service.create_from_conversation("conversation-1")

    assert conversation.state["accepted_meeting_or_visit"] is False
    assert conversation.state.get("appointment_id") is None
    assert conversation_repository.update_state.call_count == 0


def test_idempotency_key_is_stable_and_commercial_effect_is_not_duplicated():
    conversation = conversation_with_state()
    service, appointment_repository, conversation_repository = build_service(
        conversation
    )

    first = service.create_from_conversation("conversation-1")
    key = first.idempotency_key
    appointment_repository.get_by_idempotency_key.return_value = first
    second = service.create_from_conversation("conversation-1")

    assert second.idempotency_key == key
    persisted = conversation_repository.update_state.call_args.kwargs["state"]
    assert persisted["lead_score"] == 75
    assert persisted["lead_classification"] == "QUENTE"
    assert persisted["accepted_meeting_or_visit"] is True


def test_uses_lead_score_service_to_apply_commercial_effect():
    score_service = Mock()
    score_service.calculate.return_value = LeadScoreResult(
        score=88,
        classification="QUENTE",
    )
    conversation = conversation_with_state()
    service, _, conversation_repository = build_service(
        conversation,
        lead_score_service=score_service,
    )

    service.create_from_conversation("conversation-1")

    scored_state = score_service.calculate.call_args.args[0]
    assert scored_state.appointment_id == 7
    assert scored_state.accepted_meeting_or_visit is True
    persisted = conversation_repository.update_state.call_args.kwargs["state"]
    assert persisted["lead_score"] == 88
    assert persisted["lead_classification"] == "QUENTE"
