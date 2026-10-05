
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from app.database.lead_follow_up_repository import LeadFollowUpRepository
from app.database.session import SessionLocal

from app.models.appointment import Appointment
from app.models.property import Property
from app.models.lead import Lead
from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt
from app.services.lead_follow_up_service import LeadFollowUpService

TEST_IDEMPOTENCY_PREFIX = "test-follow-up-"

@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()

    test_follow_up_ids = list(
        session.scalars(
            select(LeadFollowUp.id).where(
                LeadFollowUp.idempotency_key.like(
                    f"{TEST_IDEMPOTENCY_PREFIX}%"
                )
            )
        ).all()
    )

    if test_follow_up_ids:
        session.query(LeadFollowUpAttempt).filter(
            LeadFollowUpAttempt.follow_up_id.in_(
                test_follow_up_ids
            )
        ).delete(synchronize_session=False)

        session.query(LeadFollowUp).filter(
            LeadFollowUp.id.in_(test_follow_up_ids)
        ).delete(synchronize_session=False)

        session.commit()

    session.close()


@pytest.fixture
def lead(db):
    lead = Lead(
        name="Lead Follow-up Teste",
        status="new",
    )

    db.add(lead)
    db.flush()

    return lead


def make_follow_up(lead_id: int, **overrides) -> LeadFollowUp:
    data = {
        "lead_id": lead_id,
        "status": "PENDING",
        "scheduled_at": (
                datetime.now(timezone.utc)
                - timedelta(minutes=10)
        ),
        "idempotency_key": f"{TEST_IDEMPOTENCY_PREFIX}{uuid4().hex}",
    }

    data.update(overrides)

    return LeadFollowUp(**data)


def test_create_and_find_follow_up(db, lead):
    repository = LeadFollowUpRepository(db)

    created = repository.create(
        make_follow_up(lead.id)
    )

    found = repository.get_by_id(created.id)

    assert created.id is not None
    assert found is not None
    assert found.id == created.id
    assert found.lead_id == lead.id
    assert found.status == "PENDING"
    assert found.attempt_count == 0


def test_find_by_idempotency_key(db, lead):
    repository = LeadFollowUpRepository(db)

    created = repository.create(
        make_follow_up(lead.id)
    )

    found = repository.get_by_idempotency_key(
        created.idempotency_key
    )

    assert found is not None
    assert found.id == created.id

    assert repository.get_by_idempotency_key(
        "nonexistent-key"
    ) is None


def test_list_only_due_pending_follow_ups(db, lead):
    repository = LeadFollowUpRepository(db)

    now = datetime.now(timezone.utc)

    due = repository.create(
        make_follow_up(
            lead.id,
            scheduled_at=now - timedelta(minutes=10),
        )
    )

    future = repository.create(
        make_follow_up(
            lead.id,
            scheduled_at=now + timedelta(days=1),
        )
    )

    cancelled = repository.create(
        make_follow_up(
            lead.id,
            status="CANCELLED",
            scheduled_at=now - timedelta(minutes=20),
        )
    )

    completed = repository.create(
        make_follow_up(
            lead.id,
            status="COMPLETED",
            scheduled_at=now - timedelta(minutes=30),
            completed_at=now - timedelta(minutes=5),
        )
    )

    results = repository.list_pending(now)

    result_ids = {
        item.id
        for item in results
    }

    assert due.id in result_ids

    assert future.id not in result_ids
    assert cancelled.id not in result_ids
    assert completed.id not in result_ids

def test_create_and_list_attempts(db, lead):
    repository = LeadFollowUpRepository(db)

    follow_up = repository.create(
        make_follow_up(lead.id)
    )

    now = datetime.now(timezone.utc)

    first = repository.create_attempt(
        LeadFollowUpAttempt(
            follow_up_id=follow_up.id,
            attempt_number=1,
            channel="MANUAL",
            status="FAILED",
            message="Tentativa de contato sem resposta.",
            executed_at=now,
        )
    )

    second = repository.create_attempt(
        LeadFollowUpAttempt(
            follow_up_id=follow_up.id,
            attempt_number=2,
            channel="MANUAL",
            status="SUCCESS",
            message="Contato realizado.",
            executed_at=now,
        )
    )

    attempts = repository.list_attempts(
        follow_up.id
    )

    assert first.id is not None
    assert second.id is not None

    assert [
               item.attempt_number
               for item in attempts
           ] == [1, 2]

    assert [
               item.status
               for item in attempts
           ] == [
               "FAILED",
               "SUCCESS",
           ]

def test_register_failed_attempt_with_database(db, lead):
    repository = LeadFollowUpRepository(db)

    follow_up = repository.create(
        make_follow_up(lead.id)
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
    )

    attempt = service.register_attempt(
        follow_up_id=follow_up.id,
        channel="MANUAL",
        status="FAILED",
        message="Não foi possível falar com o lead.",
    )

    db.expire_all()

    persisted_follow_up = repository.get_by_id(
        follow_up.id
    )

    attempts = repository.list_attempts(
        follow_up.id
    )

    assert attempt.id is not None
    assert attempt.attempt_number == 1
    assert attempt.status == "FAILED"

    assert persisted_follow_up is not None
    assert persisted_follow_up.attempt_count == 1
    assert persisted_follow_up.status == "PENDING"
    assert persisted_follow_up.completed_at is None

    assert len(attempts) == 1
    assert attempts[0].id == attempt.id

def test_register_successful_attempt_with_database(db, lead):
    repository = LeadFollowUpRepository(db)

    follow_up = repository.create(
        make_follow_up(lead.id)
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
    )

    attempt = service.register_attempt(
        follow_up_id=follow_up.id,
        channel="MANUAL",
        status="SUCCESS",
        message="Contato realizado com o lead.",
    )

    db.expire_all()

    persisted_follow_up = repository.get_by_id(
        follow_up.id
    )

    attempts = repository.list_attempts(
        follow_up.id
    )

    assert attempt.id is not None
    assert attempt.attempt_number == 1
    assert attempt.status == "SUCCESS"

    assert persisted_follow_up is not None
    assert persisted_follow_up.attempt_count == 1
    assert persisted_follow_up.status == "COMPLETED"
    assert persisted_follow_up.completed_at is not None

    assert len(attempts) == 1
    assert attempts[0].id == attempt.id

def test_multiple_failed_attempts_are_persisted_in_order(
        db,
        lead,
):
    repository = LeadFollowUpRepository(db)

    follow_up = repository.create(
        make_follow_up(lead.id)
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
    )

    first = service.register_attempt(
        follow_up_id=follow_up.id,
        channel="MANUAL",
        status="FAILED",
        message="Primeira tentativa sem resposta.",
    )

    second = service.register_attempt(
        follow_up_id=follow_up.id,
        channel="MANUAL",
        status="FAILED",
        message="Segunda tentativa sem resposta.",
    )

    db.expire_all()

    persisted = repository.get_by_id(follow_up.id)

    attempts = repository.list_attempts(
        follow_up.id
    )

    assert first.attempt_number == 1
    assert second.attempt_number == 2

    assert persisted is not None
    assert persisted.attempt_count == 2
    assert persisted.status == "PENDING"
    assert persisted.completed_at is None

    assert len(attempts) == 2

    assert [
               attempt.attempt_number
               for attempt in attempts
           ] == [1, 2]

    assert [
               attempt.status
               for attempt in attempts
           ] == [
               "FAILED",
               "FAILED",
           ]

def test_failed_attempt_keeps_follow_up_available_in_pending_list(
        db,
        lead,
):
    repository = LeadFollowUpRepository(db)

    now = datetime.now(timezone.utc)

    follow_up = repository.create(
        make_follow_up(
            lead.id,
            scheduled_at=now - timedelta(minutes=10),
        )
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
    )

    service.register_attempt(
        follow_up_id=follow_up.id,
        channel="MANUAL",
        status="FAILED",
        message="Lead não respondeu.",
    )

    db.expire_all()

    persisted_follow_up = repository.get_by_id(
        follow_up.id
    )

    pending_follow_ups = repository.list_pending(
        due_before=now,
    )

    pending_ids = {
        item.id
        for item in pending_follow_ups
    }

    assert persisted_follow_up is not None
    assert persisted_follow_up.status == "PENDING"
    assert persisted_follow_up.attempt_count == 1
    assert persisted_follow_up.completed_at is None

    assert follow_up.id in pending_ids

def test_successful_attempt_removes_follow_up_from_pending_list(
        db,
        lead,
):
    repository = LeadFollowUpRepository(db)

    now = datetime.now(timezone.utc)

    follow_up = repository.create(
        make_follow_up(
            lead.id,
            scheduled_at=now - timedelta(minutes=10),
        )
    )

    service = LeadFollowUpService(
        follow_up_repository=repository,
    )

    service.register_attempt(
        follow_up_id=follow_up.id,
        channel="MANUAL",
        status="SUCCESS",
        message="Contato realizado com o lead.",
    )

    db.expire_all()

    persisted_follow_up = repository.get_by_id(
        follow_up.id
    )

    pending_follow_ups = repository.list_pending(
        due_before=now,
    )

    pending_ids = {
        item.id
        for item in pending_follow_ups
    }

    assert persisted_follow_up is not None
    assert persisted_follow_up.status == "COMPLETED"
    assert persisted_follow_up.attempt_count == 1
    assert persisted_follow_up.completed_at is not None

    assert follow_up.id not in pending_ids