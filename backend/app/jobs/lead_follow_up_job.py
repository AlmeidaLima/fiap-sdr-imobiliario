from collections.abc import Callable
from datetime import datetime, timezone

from app.database.lead_follow_up_repository import (
    LeadFollowUpRepository,
)
from app.services.lead_follow_up_message_service import (
    LeadFollowUpMessageService,
)


class LeadFollowUpJob:
    def __init__(
            self,
            follow_up_repository: LeadFollowUpRepository,
            message_service: LeadFollowUpMessageService,
            now_provider: Callable[[], datetime] | None = None,
    ):
        self.follow_up_repository = follow_up_repository
        self.message_service = message_service
        self.now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def run(self) -> list[str]:
        now = self.now_provider()

        follow_ups = self.follow_up_repository.list_pending(
            due_before=now,
            limit=100,
        )

        messages = []

        for follow_up in follow_ups:
            try:
                message = self.message_service.generate(follow_up)
                messages.append(message)
            except Exception:
                continue

        return messages