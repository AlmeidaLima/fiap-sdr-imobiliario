from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.core.exceptions import ApplicationException
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.property import Property
from app.services.lead_handoff_service import LeadHandoffService


SCHEDULED_AT = datetime(2026, 10, 30, 17, 0, tzinfo=timezone.utc)


def state_data(**overrides) -> dict:
    state = {
        "lead_name": "Nome transitório",
        "commercial_intent": "COMPRA",
        "urgency_days": 30,
        "accepted_meeting_or_visit": True,
        "lead_score": 100,
        "lead_classification": "QUENTE",
        "neighborhood": "Boa Vista",
        "min_price": "250000.00",
        "max_price": "400000.00",
        "min_bedrooms": 3,
        "min_bathrooms": 2,
        "min_parking_spaces": 1,
        "min_usable_area": 70,
        "selected_property_id": 42,
        "appointment_stage": "CONFIRMED",
        "appointment_type": "REUNIAO",
        "appointment_date": "2030-01-01",
        "appointment_time": "09:15:00",
        "appointment_id": 7,
    }
    state.update(overrides)
    return state


def make_conversation(**state_overrides) -> Conversation:
    return Conversation(
        id=1,
        conversation_id="conversation-1",
        lead_id=3,
        state=state_data(**state_overrides),
    )


def make_lead(**overrides) -> Lead:
    values = {"id": 3, "name": "Rafael"}
    values.update(overrides)
    return Lead(**values)


def make_property(**overrides) -> Property:
    values = {
        "id": 42,
        "external_id": "property-external-42",
        "title": "Apartamento no Boa Vista",
        "description": "Descrição canônica",
        "usable_area": 73,
        "bathrooms": 2,
        "bedrooms": 3,
        "parking_spaces": 1,
        "amenities": [],
        "zip_code": "80000000",
        "neighborhood": "Boa Vista",
        "pois": [],
        "price": Decimal("279990.00"),
        "source": "test",
        "available": True,
    }
    values.update(overrides)
    return Property(**values)


def make_appointment(**overrides) -> Appointment:
    values = {
        "id": 7,
        "lead_id": 3,
        "property_id": 42,
        "appointment_type": "VISITA",
        "scheduled_at": SCHEDULED_AT,
        "status": "CONFIRMED",
        "idempotency_key": "key",
    }
    values.update(overrides)
    return Appointment(**values)


def build_service(
        conversation=None,
        lead=None,
        appointment=None,
        property_=None,
):
    conversation_repository = Mock()
    lead_repository = Mock()
    property_repository = Mock()
    appointment_repository = Mock()
    conversation_repository.find_by_conversation_id.return_value = conversation
    lead_repository.find_by_id.return_value = lead
    appointment_repository.get_by_id.return_value = appointment
    property_repository.find_by_id.return_value = property_

    service = LeadHandoffService(
        conversation_repository=conversation_repository,
        lead_repository=lead_repository,
        property_repository=property_repository,
        appointment_repository=appointment_repository,
    )
    return service, {
        "conversation": conversation_repository,
        "lead": lead_repository,
        "property": property_repository,
        "appointment": appointment_repository,
    }


def assert_not_ready(result):
    assert result.handoff_status == "NOT_READY"
    assert result.property is None
    assert result.appointment is None


def test_unknown_conversation_raises_controlled_error():
    service, _ = build_service()

    with pytest.raises(ApplicationException) as error:
        service.get_by_conversation_id("unknown")

    assert error.value.status_code == 404
    assert error.value.error == "conversation_not_found"


def test_conversation_without_lead_is_not_ready_with_qualification():
    conversation = make_conversation()
    conversation.lead_id = None
    service, repositories = build_service(conversation=conversation)

    result = service.get_by_conversation_id(conversation.conversation_id)

    assert_not_ready(result)
    assert result.lead is None
    assert result.qualification.commercial_intent == "COMPRA"
    assert result.qualification.max_price == Decimal("400000.00")
    repositories["lead"].find_by_id.assert_not_called()


@pytest.mark.parametrize(
    ("state_overrides", "appointment"),
    [
        ({"appointment_id": None}, make_appointment()),
        ({"accepted_meeting_or_visit": False}, make_appointment()),
        ({}, None),
        ({}, make_appointment(status="CANCELLED")),
        ({}, make_appointment(lead_id=999)),
    ],
    ids=[
        "without-appointment-id",
        "without-commercial-acceptance",
        "missing-appointment",
        "cancelled-appointment",
        "appointment-from-other-lead",
    ],
)
def test_invalid_appointment_conditions_are_not_ready(
        state_overrides,
        appointment,
):
    conversation = make_conversation(**state_overrides)
    service, _ = build_service(
        conversation=conversation,
        lead=make_lead(),
        appointment=appointment,
    )

    result = service.get_by_conversation_id(conversation.conversation_id)

    assert_not_ready(result)


@pytest.mark.parametrize(
    ("appointment", "property_", "selected_property_id"),
    [
        (make_appointment(property_id=None), None, 42),
        (make_appointment(), None, 42),
        (make_appointment(), make_property(), 99),
    ],
    ids=[
        "visit-without-property-id",
        "visit-with-missing-property",
        "visit-with-divergent-selection",
    ],
)
def test_invalid_visit_property_is_not_ready(
        appointment,
        property_,
        selected_property_id,
):
    conversation = make_conversation(
        selected_property_id=selected_property_id,
    )
    service, _ = build_service(
        conversation=conversation,
        lead=make_lead(),
        appointment=appointment,
        property_=property_,
    )

    result = service.get_by_conversation_id(conversation.conversation_id)

    assert_not_ready(result)


def test_valid_visit_is_ready_with_canonical_data():
    conversation = make_conversation(
        lead_score=75,
        lead_classification="QUENTE",
        appointment_type="REUNIAO",
        appointment_date="2030-01-01",
        appointment_time="09:15:00",
    )
    service, _ = build_service(
        conversation=conversation,
        lead=make_lead(),
        appointment=make_appointment(),
        property_=make_property(),
    )

    result = service.get_by_conversation_id(conversation.conversation_id)

    assert result.handoff_status == "READY"
    assert result.lead.id == 3
    assert result.lead.name == "Rafael"
    assert result.lead.score == 75
    assert result.lead.classification == "QUENTE"
    assert result.property.id == 42
    assert result.property.external_id == "property-external-42"
    assert result.property.price == Decimal("279990.00")
    assert result.property.bedrooms == 3
    assert result.appointment.id == 7
    assert result.appointment.appointment_type == "VISITA"
    assert result.appointment.scheduled_at == SCHEDULED_AT
    assert result.appointment.status == "CONFIRMED"


def test_valid_meeting_without_property_is_ready_with_null_property():
    conversation = make_conversation(selected_property_id=None)
    appointment = make_appointment(
        property_id=None,
        appointment_type="REUNIAO",
    )
    service, repositories = build_service(
        conversation=conversation,
        lead=make_lead(),
        appointment=appointment,
    )

    result = service.get_by_conversation_id(conversation.conversation_id)

    assert result.handoff_status == "READY"
    assert result.property is None
    assert result.appointment.appointment_type == "REUNIAO"
    repositories["property"].find_by_id.assert_not_called()


def test_valid_meeting_with_property_is_ready_with_property():
    conversation = make_conversation()
    service, _ = build_service(
        conversation=conversation,
        lead=make_lead(),
        appointment=make_appointment(appointment_type="REUNIAO"),
        property_=make_property(),
    )

    result = service.get_by_conversation_id(conversation.conversation_id)

    assert result.handoff_status == "READY"
    assert result.property.id == 42
    assert result.appointment.appointment_type == "REUNIAO"


def test_service_is_read_only_and_repeated_calls_are_equivalent():
    conversation = make_conversation()
    original_state = deepcopy(conversation.state)
    service, repositories = build_service(
        conversation=conversation,
        lead=make_lead(),
        appointment=make_appointment(),
        property_=make_property(),
    )

    first = service.get_by_conversation_id(conversation.conversation_id)
    second = service.get_by_conversation_id(conversation.conversation_id)

    assert first == second
    assert conversation.state == original_state
    assert repositories["appointment"].get_by_id.call_count == 2
    repositories["conversation"].update_state.assert_not_called()
    repositories["appointment"].create.assert_not_called()
