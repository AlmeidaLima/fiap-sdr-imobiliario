import hashlib
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ApplicationException
from app.database.lead_follow_up_repository import (
    LeadFollowUpRepository,
)
from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt


class LeadFollowUpService:
    def __init__(
            self,
            follow_up_repository: LeadFollowUpRepository,
            now_provider: Callable[[], datetime] | None = None,
    ):
        self.follow_up_repository = follow_up_repository
        self.now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def schedule(
            self,
            lead_id: int,
            scheduled_at: datetime,
            appointment_id: int | None = None,
    ) -> LeadFollowUp:
        if lead_id <= 0:
            raise ApplicationException(
                detail="Lead inválido.",
                error="invalid_lead_id",
            )

        if scheduled_at.tzinfo is None:
            raise ApplicationException(
                detail=(
                    "A data do follow-up deve possuir "
                    "informação de fuso horário."
                ),
                error="invalid_follow_up_timezone",
            )

        scheduled_at = scheduled_at.astimezone(
            timezone.utc
        )

        if scheduled_at <= self._current_utc_time():
            raise ApplicationException(
                detail=(
                    "A data do follow-up deve ser futura."
                ),
                error="follow_up_in_past",
            )

        idempotency_key = self.build_idempotency_key(
            lead_id=lead_id,
            appointment_id=appointment_id,
            scheduled_at=scheduled_at,
        )

        existing = (
            self.follow_up_repository.get_by_idempotency_key(
                idempotency_key
            )
        )

        if existing is not None:
            return existing

        follow_up = LeadFollowUp(
            lead_id=lead_id,
            appointment_id=appointment_id,
            status="PENDING",
            scheduled_at=scheduled_at,
            idempotency_key=idempotency_key,
        )

        try:
            follow_up = self.follow_up_repository.create(
                follow_up
            )

            self.follow_up_repository.commit()

            return follow_up

        except IntegrityError:
            self.follow_up_repository.rollback()

            existing = (
                self.follow_up_repository
                .get_by_idempotency_key(
                    idempotency_key
                )
            )

            if existing is not None:
                return existing

            raise

        except Exception:
            self.follow_up_repository.rollback()
            raise

    def get_by_id(
            self,
            follow_up_id: int,
    ) -> LeadFollowUp:
        follow_up = self.follow_up_repository.get_by_id(
            follow_up_id
        )

        if follow_up is None:
            raise ApplicationException(
                detail="Follow-up não encontrado.",
                status_code=404,
                error="follow_up_not_found",
            )

        return follow_up

    def cancel(
            self,
            follow_up_id: int,
    ) -> LeadFollowUp:
        follow_up = self.get_by_id(follow_up_id)

        if follow_up.status == "CANCELLED":
            return follow_up

        if follow_up.status == "COMPLETED":
            raise ApplicationException(
                detail=(
                    "Um follow-up concluído não pode "
                    "ser cancelado."
                ),
                error="follow_up_already_completed",
            )

        try:
            follow_up.status = "CANCELLED"
            follow_up.completed_at = None

            follow_up = self.follow_up_repository.update(
                follow_up
            )

            self.follow_up_repository.commit()

            return follow_up

        except Exception:
            self.follow_up_repository.rollback()
            raise

    def complete(
            self,
            follow_up_id: int,
    ) -> LeadFollowUp:
        follow_up = self.get_by_id(follow_up_id)

        if follow_up.status == "COMPLETED":
            return follow_up

        if follow_up.status == "CANCELLED":
            raise ApplicationException(
                detail=(
                    "Um follow-up cancelado não pode "
                    "ser concluído."
                ),
                error="follow_up_cancelled",
            )

        try:
            follow_up.status = "COMPLETED"
            follow_up.completed_at = (
                self._current_utc_time()
            )

            follow_up = self.follow_up_repository.update(
                follow_up
            )

            self.follow_up_repository.commit()

            return follow_up

        except Exception:
            self.follow_up_repository.rollback()
            raise

    def register_attempt(
            self,
            follow_up_id: int,
            channel: str,
            status: str,
            message: str | None = None,
    ) -> LeadFollowUpAttempt:
        if channel not in {
            "MANUAL",
            "EMAIL",
            "WHATSAPP",
        }:
            raise ApplicationException(
                detail="Canal de contato inválido.",
                error="invalid_follow_up_channel",
            )

        if status not in {
            "SUCCESS",
            "FAILED",
        }:
            raise ApplicationException(
                detail=(
                    "Resultado da tentativa inválido."
                ),
                error="invalid_follow_up_attempt_status",
            )

        try:
            follow_up = (
                self.follow_up_repository
                .get_by_id_for_update(
                    follow_up_id
                )
            )

            if follow_up is None:
                raise ApplicationException(
                    detail="Follow-up não encontrado.",
                    status_code=404,
                    error="follow_up_not_found",
                )

            if follow_up.status != "PENDING":
                raise ApplicationException(
                    detail=(
                        "O follow-up não está pendente."
                    ),
                    error="follow_up_not_pending",
                )

            executed_at = self._current_utc_time()

            attempt_number = (
                    follow_up.attempt_count + 1
            )

            attempt = LeadFollowUpAttempt(
                follow_up_id=follow_up.id,
                attempt_number=attempt_number,
                channel=channel,
                status=status,
                message=message,
                executed_at=executed_at,
            )

            attempt = (
                self.follow_up_repository
                .create_attempt(
                    attempt
                )
            )

            follow_up.attempt_count = (
                attempt_number
            )

            # SUCCESS significa que houve
            # contato efetivo com o lead.
            if status == "SUCCESS":
                follow_up.status = "COMPLETED"
                follow_up.completed_at = (
                    executed_at
                )

            self.follow_up_repository.update(
                follow_up
            )

            self.follow_up_repository.commit()

            return attempt

        except Exception:
            self.follow_up_repository.rollback()
            raise

    @staticmethod
    def build_idempotency_key(
            lead_id: int,
            appointment_id: int | None,
            scheduled_at: datetime,
    ) -> str:
        canonical_value = "|".join(
            [
                str(lead_id),
                str(appointment_id or ""),
                scheduled_at
                .astimezone(timezone.utc)
                .isoformat(),
            ]
        )

        return hashlib.sha256(
            canonical_value.encode("utf-8")
        ).hexdigest()

    def _current_utc_time(self) -> datetime:
        current = self.now_provider()

        if current.tzinfo is None:
            current = current.replace(
                tzinfo=timezone.utc
            )

        return current.astimezone(
            timezone.utc
        )