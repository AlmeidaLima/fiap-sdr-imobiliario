from app.database.conversation_repository import ConversationRepository
from app.database.lead_follow_up_repository import (
    LeadFollowUpRepository,
)
from app.database.message_repository import MessageRepository
from app.database.session import SessionLocal
from app.jobs.lead_follow_up_job import LeadFollowUpJob
from app.models.appointment import Appointment  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.property import Property  # noqa: F401
from app.services.lead_follow_up_message_service import (
    LeadFollowUpMessageService,
)
from app.services.lead_follow_up_delivery_service import (
    LeadFollowUpDeliveryService,
)


def process_lead_follow_ups():
    db = SessionLocal()

    try:
        repository = LeadFollowUpRepository(db)
        message_service = LeadFollowUpMessageService()
        delivery_service = LeadFollowUpDeliveryService(
            follow_up_repository=repository,
            conversation_repository=ConversationRepository(db),
            message_repository=MessageRepository(db),
            message_service=message_service,
        )

        job = LeadFollowUpJob(
            follow_up_repository=repository,
            delivery_service=delivery_service,
        )

        result = job.run()

        print("=" * 60)
        print("PROCESSAMENTO MANUAL DE FOLLOW-UPS")
        print("=" * 60)
        print(f"Follow-ups processados: {result.processed}")
        print(f"Follow-ups entregues: {result.delivered}")
        print(f"Follow-ups ignorados: {result.skipped}")
        print(f"Follow-ups com falha: {result.failed}")

        print()
        print("=" * 60)

        return result

    finally:
        db.close()


if __name__ == "__main__":
    process_lead_follow_ups()
