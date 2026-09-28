from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.flush()
        self.db.refresh(appointment)
        return appointment

    def get_by_id(self, appointment_id: int) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def get_by_idempotency_key(
            self,
            idempotency_key: str,
    ) -> Appointment | None:
        statement = select(Appointment).where(
            Appointment.idempotency_key == idempotency_key
        )
        return self.db.scalar(statement)

    def rollback(self) -> None:
        self.db.rollback()
