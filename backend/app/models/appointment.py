from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.property import Property


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "appointment_type IN ('VISITA', 'REUNIAO')",
            name="ck_appointments_type",
        ),
        CheckConstraint(
            "status IN ('CONFIRMED', 'CANCELLED')",
            name="ck_appointments_status",
        ),
        CheckConstraint(
            "appointment_type != 'VISITA' OR property_id IS NOT NULL",
            name="ck_appointments_visit_property",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[int | None] = mapped_column(
        ForeignKey("properties.id"),
        nullable=True,
        index=True,
    )
    appointment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="CONFIRMED",
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    lead: Mapped["Lead"] = relationship("Lead")
    property: Mapped["Property | None"] = relationship("Property")
