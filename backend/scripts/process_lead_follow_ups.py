from app.database.lead_follow_up_repository import (
    LeadFollowUpRepository,
)
from app.database.session import SessionLocal
from app.jobs.lead_follow_up_job import LeadFollowUpJob
from app.services.lead_follow_up_message_service import (
    LeadFollowUpMessageService,
)


def process_lead_follow_ups() -> list[str]:
    db = SessionLocal()

    try:
        repository = LeadFollowUpRepository(db)
        message_service = LeadFollowUpMessageService()

        job = LeadFollowUpJob(
            follow_up_repository=repository,
            message_service=message_service,
        )

        messages = job.run()

        print("=" * 60)
        print("PROCESSAMENTO MANUAL DE FOLLOW-UPS")
        print("=" * 60)
        print(f"Follow-ups processados: {len(messages)}")

        for index, message in enumerate(messages, start=1):
            print()
            print(f"[{index}] {message}")

        print()
        print("=" * 60)

        return messages

    finally:
        db.close()


if __name__ == "__main__":
    process_lead_follow_ups()