import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic

from app.database.lead_follow_up_repository import LeadFollowUpRepository
from app.services.lead_follow_up_delivery_service import (
    LeadFollowUpDeliveryService,
)


@dataclass(frozen=True)
class LeadFollowUpJobResult:
    processed: int = 0
    delivered: int = 0
    skipped: int = 0
    failed: int = 0


class LeadFollowUpJob:
    BATCH_SIZE = 100

    def __init__(
            self,
            follow_up_repository: LeadFollowUpRepository,
            delivery_service: LeadFollowUpDeliveryService,
            now_provider: Callable[[], datetime] | None = None,
            logger: logging.Logger | None = None,
            should_stop: Callable[[], bool] | None = None,
    ):
        self.follow_up_repository = follow_up_repository
        self.delivery_service = delivery_service
        self.now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self.logger = logger or logging.getLogger(__name__)
        self.should_stop = should_stop or (lambda: False)

    def run(self) -> LeadFollowUpJobResult:
        cycle_started_at = self.now_provider()
        started = monotonic()
        cursor: tuple[datetime, int] | None = None
        processed = delivered = skipped = failed = 0
        page_processed = 0

        self.logger.info(
            "follow_up_cycle_started",
            extra={"batch_size": self.BATCH_SIZE},
        )

        while True:
            if self.should_stop():
                break

            try:
                follow_up = self.follow_up_repository.claim_next_pending(
                    due_before=cycle_started_at,
                    cursor=cursor,
                )
            except Exception:
                self.follow_up_repository.rollback()
                raise

            if follow_up is None:
                break

            cursor = (follow_up.scheduled_at, follow_up.id)
            follow_up_id = follow_up.id
            lead_id = follow_up.lead_id
            processed += 1
            page_processed += 1
            self.logger.info(
                "follow_up_processing_started",
                extra={
                    "follow_up_id": follow_up_id,
                    "lead_id": lead_id,
                },
            )

            try:
                result = self.delivery_service.deliver_claimed(
                    follow_up=follow_up,
                    due_before=cycle_started_at,
                )
                if result is None:
                    skipped += 1
                    self.logger.info(
                        "follow_up_skipped",
                        extra={
                            "follow_up_id": follow_up_id,
                            "lead_id": lead_id,
                            "status": "PENDING",
                        },
                    )
                else:
                    delivered += 1
                    self.logger.info(
                        "follow_up_delivered",
                        extra={
                            "follow_up_id": follow_up_id,
                            "lead_id": lead_id,
                            "conversation_id": result.conversation_id,
                            "attempt_number": result.attempt.attempt_number,
                            "status": "COMPLETED",
                        },
                    )
            except Exception as exc:
                failed += 1
                self.logger.error(
                    "follow_up_processing_failed",
                    extra={
                        "follow_up_id": follow_up_id,
                        "lead_id": lead_id,
                        "error_type": type(exc).__name__,
                    },
                )

            if page_processed == self.BATCH_SIZE:
                self.logger.info(
                    "follow_up_batch_completed",
                    extra={
                        "batch_size": self.BATCH_SIZE,
                        "processed": page_processed,
                    },
                )
                page_processed = 0

        if page_processed:
            self.logger.info(
                "follow_up_batch_completed",
                extra={
                    "batch_size": self.BATCH_SIZE,
                    "processed": page_processed,
                },
            )

        result = LeadFollowUpJobResult(
            processed=processed,
            delivered=delivered,
            skipped=skipped,
            failed=failed,
        )
        self.logger.info(
            "follow_up_cycle_completed",
            extra={
                "processed": processed,
                "delivered": delivered,
                "skipped": skipped,
                "failed": failed,
                "duration_ms": round((monotonic() - started) * 1000),
            },
        )
        return result
