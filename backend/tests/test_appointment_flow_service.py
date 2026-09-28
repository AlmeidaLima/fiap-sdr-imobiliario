from datetime import date, time

import pytest

from app.schemas.conversation import ConversationState
from app.services.appointment_flow_service import AppointmentFlowService


def create_state(**updates) -> ConversationState:
    state = ConversationState(
        conversation_id="appointment-flow",
        presented_property_ids=[10, 20],
        selected_property_id=10,
        appointment_stage="SELECTED",
        lead_score=50,
    )
    return state.model_copy(update=updates)


def create_service() -> AppointmentFlowService:
    return AppointmentFlowService(
        today_provider=lambda: date(2026, 9, 27),
    )


def test_selected_property_starts_awaiting_type_without_commercial_effects():
    state = create_state()

    result = create_service().process(state, "Tenho interesse")

    assert result.state.appointment_stage == "AWAITING_TYPE"
    assert result.state.accepted_meeting_or_visit is False
    assert result.state.lead_score == 50
    assert state.appointment_stage == "SELECTED"


@pytest.mark.parametrize(
    ("message", "expected_type"),
    [
        ("Quero marcar uma visita", "VISITA"),
        ("Prefiro uma reunião", "REUNIAO"),
    ],
)
def test_records_explicit_appointment_type(message, expected_type):
    state = create_state(appointment_stage="AWAITING_TYPE")

    result = create_service().process(state, message)

    assert result.state.appointment_type == expected_type
    assert result.state.appointment_stage == "AWAITING_DATE"
    assert result.state.accepted_meeting_or_visit is False


def test_records_valid_date_and_serializes_state():
    state = create_state(
        appointment_stage="AWAITING_DATE",
        appointment_type="VISITA",
    )

    result = create_service().process(state, "30/09/2026")

    assert result.state.appointment_date == date(2026, 9, 30)
    assert result.state.appointment_stage == "AWAITING_TIME"
    serialized = result.state.model_dump(mode="json")
    recovered = ConversationState.model_validate(serialized)
    assert recovered.appointment_date == date(2026, 9, 30)


@pytest.mark.parametrize("message", ["26/09/2026", "31/09/2026"])
def test_rejects_past_or_invalid_date_without_destroying_state(message):
    previous_date = date(2026, 10, 1)
    state = create_state(
        appointment_stage="AWAITING_DATE",
        appointment_type="VISITA",
        appointment_date=previous_date,
    )

    result = create_service().process(state, message)

    assert result.state.appointment_stage == "AWAITING_DATE"
    assert result.state.appointment_date == previous_date


@pytest.mark.parametrize(
    ("message", "expected_time"),
    [
        ("14:00", time(14, 0)),
        ("14h", time(14, 0)),
        ("14h30", time(14, 30)),
    ],
)
def test_records_supported_time_formats(message, expected_time):
    state = create_state(
        appointment_stage="AWAITING_TIME",
        appointment_type="VISITA",
        appointment_date=date(2026, 9, 30),
    )

    result = create_service().process(state, message)

    assert result.state.appointment_time == expected_time
    assert result.state.appointment_stage == "AWAITING_CONFIRMATION"
    assert "30/09/2026" in result.response
    assert expected_time.strftime("%H:%M") in result.response


@pytest.mark.parametrize("message", ["25:00", "14:99"])
def test_rejects_invalid_time_without_destroying_state(message):
    previous_time = time(10, 0)
    state = create_state(
        appointment_stage="AWAITING_TIME",
        appointment_type="VISITA",
        appointment_date=date(2026, 9, 30),
        appointment_time=previous_time,
    )

    result = create_service().process(state, message)

    assert result.state.appointment_stage == "AWAITING_TIME"
    assert result.state.appointment_time == previous_time


def create_confirmation_state() -> ConversationState:
    return create_state(
        appointment_stage="AWAITING_CONFIRMATION",
        appointment_type="VISITA",
        appointment_date=date(2026, 9, 30),
        appointment_time=time(14, 0),
    )


@pytest.mark.parametrize("message", ["sim", "confirmo", "pode confirmar"])
def test_confirmation_is_deterministic_and_has_no_commercial_effect(message):
    state = create_confirmation_state()

    result = create_service().process(state, message)

    assert result.state.appointment_stage == "CONFIRMED"
    assert result.state.accepted_meeting_or_visit is False
    assert result.state.lead_score == 50
    assert result.response == (
        "Dados do agendamento confirmados para 30/09/2026 às 14:00. "
        "Finalizando o agendamento..."
    )
    assert "agendada com sucesso" not in result.response.lower()


def test_repeated_confirmation_is_idempotent():
    confirmed = create_service().process(
        create_confirmation_state(),
        "confirmo",
    ).state

    repeated = create_service().process(confirmed, "confirmo")

    assert repeated.state == confirmed
    assert repeated.state.accepted_meeting_or_visit is False


@pytest.mark.parametrize("message", ["não", "cancelar", "não quero mais"])
def test_cancellation_has_no_commercial_effect(message):
    state = create_confirmation_state()

    result = create_service().process(state, message)

    assert result.state.appointment_stage == "CANCELLED"
    assert result.state.selected_property_id == 10
    assert result.state.accepted_meeting_or_visit is False
    assert result.state.lead_score == 50


def test_old_state_uses_appointment_defaults():
    state = ConversationState.model_validate(
        {"conversation_id": "old-conversation"}
    )

    assert state.appointment_stage == "NONE"
    assert state.appointment_type is None
    assert state.appointment_date is None
    assert state.appointment_time is None
