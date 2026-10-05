
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt


class LeadFollowUpRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, follow_up: LeadFollowUp) -> LeadFollowUp:
        self.db.add(follow_up)
        self.db.flush()
        self.db.refresh(follow_up)
        return follow_up

    def get_by_id(self, follow_up_id: int) -> LeadFollowUp | None:
        return self.db.get(LeadFollowUp, follow_up_id)
    def get_by_id_for_update(
            self,
            follow_up_id: int,
    ) -> LeadFollowUp | None:
        statement = (
            select(LeadFollowUp)
            .where(LeadFollowUp.id == follow_up_id)
            .with_for_update()
        )

        return self.db.scalar(statement)

    def get_by_idempotency_key(
            self,
            idempotency_key: str,
    ) -> LeadFollowUp | None:
        statement = select(LeadFollowUp).where(
            LeadFollowUp.idempotency_key == idempotency_key
        )
        return self.db.scalar(statement)

    def list_pending(
            self,
            due_before: datetime,
            limit: int = 100,
    ) -> list[LeadFollowUp]:
        statement = (
            select(LeadFollowUp)
            .where(
                LeadFollowUp.status == "PENDING",
                LeadFollowUp.scheduled_at <= due_before,
                )
            .order_by(
                LeadFollowUp.scheduled_at,
                LeadFollowUp.id,
            )
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def create_attempt(
            self,
            attempt: LeadFollowUpAttempt,
    ) -> LeadFollowUpAttempt:
        self.db.add(attempt)
        self.db.flush()
        self.db.refresh(attempt)
        return attempt

    def list_attempts(
            self,
            follow_up_id: int,
    ) -> list[LeadFollowUpAttempt]:
        statement = (
            select(LeadFollowUpAttempt)
            .where(
                LeadFollowUpAttempt.follow_up_id == follow_up_id
            )
            .order_by(LeadFollowUpAttempt.attempt_number)
        )
        return list(self.db.scalars(statement).all())

    def update(self, follow_up: LeadFollowUp) -> LeadFollowUp:
        self.db.add(follow_up)
        self.db.flush()
        self.db.refresh(follow_up)
        return follow_up

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
