from datetime import datetime, timedelta, timezone

from app.models.appointment import Appointment
from app.models.lead import Lead
from app.models.property import Property
from app.models.lead_follow_up import LeadFollowUp
from app.services.lead_follow_up_message_service import (
    LeadFollowUpMessageService,
)


NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def test_generate_message_without_appointment():
    lead = Lead(
        id=10,
        name="Rafael",
        status="new",
    )

    follow_up = LeadFollowUp(
        id=5,
        lead_id=lead.id,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="message-test",
    )

    follow_up.lead = lead
    follow_up.appointment = None

    service = LeadFollowUpMessageService()

    result = service.generate(follow_up)

    assert result == (
        "Olá, Rafael! "
        "Estou entrando em contato para dar continuidade "
        "ao seu atendimento. Podemos conversar?"
    )

def test_generate_message_without_lead_name():
    lead = Lead(
        id=10,
        name=None,
        status="new",
    )

    follow_up = LeadFollowUp(
        id=5,
        lead_id=lead.id,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="message-test-without-name",
    )

    follow_up.lead = lead
    follow_up.appointment = None

    service = LeadFollowUpMessageService()

    result = service.generate(follow_up)

    assert result == (
        "Olá! "
        "Estou entrando em contato para dar continuidade "
        "ao seu atendimento. Podemos conversar?"
    )

def test_generate_message_for_visit_appointment():
    lead = Lead(
        id=10,
        name="Rafael",
        status="new",
    )

    appointment = Appointment(
        id=20,
        lead_id=lead.id,
        appointment_type="VISITA",
        scheduled_at=NOW + timedelta(days=2),
        status="CONFIRMED",
        idempotency_key="appointment-visit-test",
    )

    follow_up = LeadFollowUp(
        id=5,
        lead_id=lead.id,
        appointment_id=appointment.id,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="message-visit-test",
    )

    follow_up.lead = lead
    follow_up.appointment = appointment

    service = LeadFollowUpMessageService()

    result = service.generate(follow_up)

    assert result == (
        "Olá, Rafael! "
        "Estou entrando em contato para dar continuidade "
        "ao atendimento sobre sua visita. Podemos conversar?"
    )

def test_generate_message_for_meeting_appointment():
    lead = Lead(
        id=10,
        name="Rafael",
        status="new",
    )

    appointment = Appointment(
        id=20,
        lead_id=lead.id,
        appointment_type="REUNIAO",
        scheduled_at=NOW + timedelta(days=2),
        status="CONFIRMED",
        idempotency_key="appointment-meeting-test",
    )

    follow_up = LeadFollowUp(
        id=5,
        lead_id=lead.id,
        appointment_id=appointment.id,
        status="PENDING",
        scheduled_at=NOW + timedelta(days=1),
        idempotency_key="message-meeting-test",
    )

    follow_up.lead = lead
    follow_up.appointment = appointment

    service = LeadFollowUpMessageService()

    result = service.generate(follow_up)

    assert result == (
        "Olá, Rafael! "
        "Estou entrando em contato para dar continuidade "
        "ao atendimento sobre nossa reunião. Podemos conversar?"
    )