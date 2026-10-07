from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from app.database.conversation_repository import ConversationRepository
from app.database.lead_follow_up_repository import LeadFollowUpRepository
from app.database.message_repository import MessageRepository
from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt
from app.models.message import Message
from app.services.lead_follow_up_message_service import LeadFollowUpMessageService


@dataclass(frozen=True)
class LeadFollowUpDelivery:
    message: Message
    attempt: LeadFollowUpAttempt
    conversation_id: str


class LeadFollowUpDeliveryService:
    def __init__(
            self,
            follow_up_repository: LeadFollowUpRepository,
            conversation_repository: ConversationRepository,
            message_repository: MessageRepository,
            message_service: LeadFollowUpMessageService,
            now_provider: Callable[[], datetime] | None = None,
    ):
        self.follow_up_repository = follow_up_repository
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.message_service = message_service
        self.now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def deliver_claimed(
            self,
            follow_up: LeadFollowUp,
            due_before: datetime,
    ) -> LeadFollowUpDelivery | None:
        try:
            if (
                follow_up.status != "PENDING"
                or follow_up.scheduled_at > due_before
            ):
                self.follow_up_repository.rollback()
                return None

            conversation = (
                self.conversation_repository.find_latest_by_lead_id(
                    follow_up.lead_id
                )
            )
            if conversation is None:
                self.follow_up_repository.rollback()
                return None

            content = self.message_service.generate(follow_up)
            message = self.message_repository.create_without_commit(
                conversation_id=conversation.id,
                role="assistant",
                content=content,
            )

            executed_at = self._current_utc_time()
            attempt_number = follow_up.attempt_count + 1
            attempt = self.follow_up_repository.create_attempt(
                LeadFollowUpAttempt(
                    follow_up_id=follow_up.id,
                    attempt_number=attempt_number,
                    channel="WEB",
                    status="SUCCESS",
                    message=content,
                    executed_at=executed_at,
                )
            )
            follow_up.attempt_count = attempt_number
            follow_up.status = "COMPLETED"
            follow_up.completed_at = executed_at
            self.follow_up_repository.update(follow_up)
            self.follow_up_repository.commit()

            return LeadFollowUpDelivery(
                message=message,
                attempt=attempt,
                conversation_id=conversation.conversation_id,
            )
        except Exception:
            self.follow_up_repository.rollback()
            raise

    def _current_utc_time(self) -> datetime:
        current = self.now_provider()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc)
