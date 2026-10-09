from datetime import datetime, timedelta, timezone
import threading
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.database.conversation_repository import ConversationRepository
from app.database.lead_follow_up_repository import LeadFollowUpRepository
from app.database.message_repository import MessageRepository
from app.database.session import SessionLocal
from app.models.conversation import Conversation
from app.models.appointment import Appointment  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.property import Property  # noqa: F401
from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt
from app.models.message import Message
from app.services.lead_follow_up_delivery_service import (
    LeadFollowUpDeliveryService,
)
from app.services.lead_follow_up_message_service import LeadFollowUpMessageService


NOW = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)


def make_service():
    follow_up_repository = Mock()
    conversation_repository = Mock()
    message_repository = Mock()
    message_service = Mock()
    service = LeadFollowUpDeliveryService(
        follow_up_repository=follow_up_repository,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        message_service=message_service,
        now_provider=lambda: NOW,
    )
    return (
        service,
        follow_up_repository,
        conversation_repository,
        message_repository,
        message_service,
    )


def pending_follow_up():
    return LeadFollowUp(
        id=5,
        lead_id=10,
        status="PENDING",
        scheduled_at=NOW - timedelta(minutes=1),
        attempt_count=0,
        idempotency_key="delivery-test",
    )


def test_success_is_committed_once_with_all_effects():
    service, repository, conversations, messages, generator = make_service()
    item = pending_follow_up()
    conversation = Conversation(id=20, conversation_id="web-chat", state={})
    conversations.find_latest_by_lead_id.return_value = conversation
    generator.generate.return_value = "Follow-up"
    persisted_message = Mock(id=30)
    messages.create_without_commit.return_value = persisted_message
    repository.create_attempt.side_effect = lambda attempt: attempt
    repository.update.side_effect = lambda follow_up: follow_up

    result = service.deliver_claimed(item, NOW)

    assert result is not None
    assert result.message is persisted_message
    assert result.attempt.channel == "WEB"
    assert result.attempt.status == "SUCCESS"
    assert result.attempt.attempt_number == 1
    assert item.attempt_count == 1
    assert item.status == "COMPLETED"
    assert item.completed_at == NOW
    repository.commit.assert_called_once_with()
    repository.rollback.assert_not_called()


@pytest.mark.parametrize(
    "failure_target",
    ["generate", "message", "attempt", "update", "commit"],
)
def test_any_delivery_failure_rolls_back_without_failed_attempt(failure_target):
    service, repository, conversations, messages, generator = make_service()
    item = pending_follow_up()
    conversations.find_latest_by_lead_id.return_value = Conversation(
        id=20,
        conversation_id="web-chat",
        state={},
    )
    generator.generate.return_value = "Follow-up"
    messages.create_without_commit.return_value = Mock(id=30)
    repository.create_attempt.side_effect = lambda attempt: attempt
    repository.update.side_effect = lambda follow_up: follow_up
    target = {
        "generate": generator.generate,
        "message": messages.create_without_commit,
        "attempt": repository.create_attempt,
        "update": repository.update,
        "commit": repository.commit,
    }[failure_target]
    target.side_effect = RuntimeError("technical failure")

    with pytest.raises(RuntimeError):
        service.deliver_claimed(item, NOW)

    repository.rollback.assert_called_once_with()
    failed_attempts = [
        call.args[0]
        for call in repository.create_attempt.call_args_list
        if call.args[0].status == "FAILED"
    ]
    assert failed_attempts == []


def test_missing_conversation_keeps_follow_up_pending():
    service, repository, conversations, messages, generator = make_service()
    item = pending_follow_up()
    conversations.find_latest_by_lead_id.return_value = None

    assert service.deliver_claimed(item, NOW) is None
    assert item.status == "PENDING"
    assert item.attempt_count == 0
    messages.create_without_commit.assert_not_called()
    generator.generate.assert_not_called()
    repository.create_attempt.assert_not_called()
    repository.commit.assert_not_called()
    repository.rollback.assert_called_once_with()


@pytest.mark.parametrize("status", ["CANCELLED", "COMPLETED"])
def test_non_pending_follow_up_is_skipped(status):
    service, repository, conversations, messages, _ = make_service()
    item = pending_follow_up()
    item.status = status
    assert service.deliver_claimed(item, NOW) is None
    conversations.find_latest_by_lead_id.assert_not_called()
    messages.create_without_commit.assert_not_called()
    repository.rollback.assert_called_once_with()


def create_real_delivery_data(prefix: str):
    db = SessionLocal()
    lead = Lead(name=f"{prefix} lead", status="new")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    conversation = ConversationRepository(db).create(
        conversation_id=f"{prefix}-{uuid4()}",
        lead_id=lead.id,
    )
    follow_up = LeadFollowUp(
        lead_id=lead.id,
        status="PENDING",
        scheduled_at=NOW - timedelta(minutes=1),
        attempt_count=0,
        idempotency_key=f"{prefix}-{uuid4()}",
    )
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    ids = (lead.id, conversation.id, follow_up.id)
    db.close()
    return ids


def remove_real_delivery_data(lead_id: int, conversation_id: int, follow_up_id: int):
    db = SessionLocal()
    try:
        db.query(LeadFollowUpAttempt).filter_by(follow_up_id=follow_up_id).delete()
        db.query(Message).filter_by(conversation_id=conversation_id).delete()
        db.query(LeadFollowUp).filter_by(id=follow_up_id).delete()
        db.query(Conversation).filter_by(id=conversation_id).delete()
        db.query(Lead).filter_by(id=lead_id).delete()
        db.commit()
    finally:
        db.close()


def real_delivery_service(db, repository=None):
    repository = repository or LeadFollowUpRepository(db)
    return LeadFollowUpDeliveryService(
        follow_up_repository=repository,
        conversation_repository=ConversationRepository(db),
        message_repository=MessageRepository(db),
        message_service=LeadFollowUpMessageService(),
        now_provider=lambda: NOW,
    )


def test_real_transaction_rolls_back_all_delivery_effects_before_commit():
    lead_id, conversation_id, follow_up_id = create_real_delivery_data(
        "atomic-web"
    )

    class FailingCommitRepository(LeadFollowUpRepository):
        def commit(self):
            raise RuntimeError("forced failure before commit")

    db = SessionLocal()
    try:
        repository = FailingCommitRepository(db)
        follow_up = repository.claim_next_pending(NOW)
        with pytest.raises(RuntimeError):
            real_delivery_service(db, repository).deliver_claimed(follow_up, NOW)
    finally:
        db.close()

    verification = SessionLocal()
    try:
        persisted = verification.get(LeadFollowUp, follow_up_id)
        assert persisted.status == "PENDING"
        assert persisted.attempt_count == 0
        assert persisted.completed_at is None
        assert verification.scalar(select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id
        )) == 0
        assert verification.scalar(select(func.count(LeadFollowUpAttempt.id)).where(
            LeadFollowUpAttempt.follow_up_id == follow_up_id
        )) == 0
    finally:
        verification.close()
        remove_real_delivery_data(lead_id, conversation_id, follow_up_id)


def test_two_real_sessions_deliver_same_follow_up_only_once():
    lead_id, conversation_id, follow_up_id = create_real_delivery_data(
        "concurrent-web"
    )
    acquired = threading.Event()
    release = threading.Event()
    errors: list[Exception] = []

    class HoldingRepository(LeadFollowUpRepository):
        def claim_next_pending(self, due_before, cursor=None):
            item = super().claim_next_pending(due_before, cursor)
            if item is not None:
                acquired.set()
                release.wait(timeout=10)
            return item

    def run_job(repository_class):
        db = SessionLocal()
        try:
            repository = repository_class(db)
            from app.jobs.lead_follow_up_job import LeadFollowUpJob
            LeadFollowUpJob(
                follow_up_repository=repository,
                delivery_service=real_delivery_service(db, repository),
                now_provider=lambda: NOW,
            ).run()
        except Exception as exc:
            errors.append(exc)
        finally:
            db.close()

    first = threading.Thread(target=run_job, args=(HoldingRepository,))
    second = threading.Thread(target=run_job, args=(LeadFollowUpRepository,))
    first.start()
    assert acquired.wait(timeout=10)
    second.start()
    second.join(timeout=10)
    release.set()
    first.join(timeout=10)

    verification = SessionLocal()
    try:
        persisted = verification.get(LeadFollowUp, follow_up_id)
        attempts = list(verification.scalars(select(LeadFollowUpAttempt).where(
            LeadFollowUpAttempt.follow_up_id == follow_up_id
        )))
        messages = list(verification.scalars(select(Message).where(
            Message.conversation_id == conversation_id,
            Message.role == "assistant",
        )))
        assert errors == []
        assert not first.is_alive()
        assert not second.is_alive()
        assert len(messages) == 1
        assert len(attempts) == 1
        assert attempts[0].channel == "WEB"
        assert attempts[0].status == "SUCCESS"
        assert persisted.attempt_count == 1
        assert persisted.status == "COMPLETED"
    finally:
        verification.close()
        remove_real_delivery_data(lead_id, conversation_id, follow_up_id)
