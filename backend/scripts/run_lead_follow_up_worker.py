import logging
import signal
import threading

from app.core.observability import configure_logging
from app.database.conversation_repository import ConversationRepository
from app.database.lead_follow_up_repository import LeadFollowUpRepository
from app.database.message_repository import MessageRepository
from app.database.session import SessionLocal
from app.jobs.lead_follow_up_job import LeadFollowUpJob
from app.models.appointment import Appointment  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.property import Property  # noqa: F401
from app.services.lead_follow_up_delivery_service import (
    LeadFollowUpDeliveryService,
)
from app.services.lead_follow_up_message_service import (
    LeadFollowUpMessageService,
)


INTERVAL_SECONDS = 30
LOGGER = logging.getLogger("follow_up_worker")


def _create_job(db, should_stop=None) -> LeadFollowUpJob:
    follow_up_repository = LeadFollowUpRepository(db)
    delivery_service = LeadFollowUpDeliveryService(
        follow_up_repository=follow_up_repository,
        conversation_repository=ConversationRepository(db),
        message_repository=MessageRepository(db),
        message_service=LeadFollowUpMessageService(),
    )
    return LeadFollowUpJob(
        follow_up_repository=follow_up_repository,
        delivery_service=delivery_service,
        logger=LOGGER,
        should_stop=should_stop,
    )


def run_worker(
        stop_event: threading.Event | None = None,
        interval_seconds: int = INTERVAL_SECONDS,
) -> None:
    stop_event = stop_event or threading.Event()

    def request_shutdown(signum, _frame) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    LOGGER.info(
        "follow_up_worker_started",
        extra={
            "interval_seconds": interval_seconds,
            "batch_size": LeadFollowUpJob.BATCH_SIZE,
        },
    )

    while not stop_event.is_set():
        db = SessionLocal()
        try:
            _create_job(db, should_stop=stop_event.is_set).run()
        except Exception as exc:
            db.rollback()
            LOGGER.error(
                "follow_up_database_unavailable",
                extra={"error_type": type(exc).__name__},
            )
        finally:
            db.close()

        stop_event.wait(interval_seconds)

    LOGGER.info("follow_up_worker_stopping")
    LOGGER.info("follow_up_worker_stopped")


def main() -> None:
    configure_logging("follow_up_worker")
    run_worker()


if __name__ == "__main__":
    main()
