from datetime import datetime, timezone
from uuid import uuid4

from app.database.appointment_repository import AppointmentRepository
from app.database.lead_repository import LeadRepository
from app.database.session import SessionLocal
from app.models.appointment import Appointment
from app.models.lead import Lead


def test_list_by_lead_id_filters_and_orders_without_modifying_state():
    db = SessionLocal()
    appointments = []
    leads = []
    token = uuid4().hex
    try:
        first_lead = LeadRepository(db).create(name="Lead principal")
        other_lead = LeadRepository(db).create(name="Outro lead")
        leads.extend([first_lead, other_lead])
        same_schedule = datetime(2099, 12, 31, 15, 0, tzinfo=timezone.utc)
        older = Appointment(
            lead_id=first_lead.id,
            appointment_type="REUNIAO",
            scheduled_at=datetime(2099, 12, 30, 15, 0, tzinfo=timezone.utc),
            status="CONFIRMED",
            idempotency_key=f"repository-{token}-older",
        )
        same_schedule_first = Appointment(
            lead_id=first_lead.id,
            appointment_type="REUNIAO",
            scheduled_at=same_schedule,
            status="CONFIRMED",
            idempotency_key=f"repository-{token}-first",
        )
        same_schedule_higher_id = Appointment(
            lead_id=first_lead.id,
            appointment_type="REUNIAO",
            scheduled_at=same_schedule,
            status="CANCELLED",
            idempotency_key=f"repository-{token}-higher-id",
        )
        other = Appointment(
            lead_id=other_lead.id,
            appointment_type="REUNIAO",
            scheduled_at=datetime(2100, 1, 1, 15, 0, tzinfo=timezone.utc),
            status="CONFIRMED",
            idempotency_key=f"repository-{token}-other",
        )
        appointments.extend([
            older,
            same_schedule_first,
            same_schedule_higher_id,
            other,
        ])
        db.add_all(appointments)
        db.commit()

        original_statuses = {
            appointment.id: appointment.status for appointment in appointments
        }
        results = AppointmentRepository(db).list_by_lead_id(first_lead.id)

        assert [appointment.id for appointment in results] == [
            same_schedule_higher_id.id,
            same_schedule_first.id,
            older.id,
        ]
        assert all(
            appointment.lead_id == first_lead.id for appointment in results
        )
        assert {
            appointment.id: appointment.status for appointment in appointments
        } == original_statuses
        assert not db.dirty
    finally:
        for appointment in appointments:
            persisted = db.get(Appointment, appointment.id)
            if persisted is not None:
                db.delete(persisted)
        db.flush()
        for lead in leads:
            persisted = db.get(Lead, lead.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()
