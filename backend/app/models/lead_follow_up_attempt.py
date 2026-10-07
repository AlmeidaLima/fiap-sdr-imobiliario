from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead_follow_up import LeadFollowUp


class LeadFollowUpAttempt(Base):
    __tablename__ = "lead_follow_up_attempts"

    __table_args__ = (
        CheckConstraint(
            "attempt_number >= 1",
            name="ck_lead_follow_up_attempts_number",
        ),
        CheckConstraint(
            "channel IN ('MANUAL', 'EMAIL', 'WHATSAPP', 'WEB')",
            name="ck_lead_follow_up_attempts_channel",
        ),
        CheckConstraint(
            "status IN ('SUCCESS', 'FAILED')",
            name="ck_lead_follow_up_attempts_status",
        ),
        UniqueConstraint(
            "follow_up_id",
            "attempt_number",
            name="uq_lead_follow_up_attempts_number",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    follow_up_id: Mapped[int] = mapped_column(
        ForeignKey("lead_follow_ups.id"),
        nullable=False,
        index=True,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    follow_up: Mapped["LeadFollowUp"] = relationship("LeadFollowUp")
