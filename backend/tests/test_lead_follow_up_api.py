from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.lead import Lead
from app.models.lead_follow_up import LeadFollowUp
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt


client = TestClient(app)

TEST_PREFIX = "follow-up-api-test-"

_created_lead_ids: list[int] = []


@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield

    if not _created_lead_ids:
        return

    db = SessionLocal()

    try:
        lead_ids = list(_created_lead_ids)

        follow_up_ids = list(
            db.scalars(
                select(LeadFollowUp.id).where(
                    LeadFollowUp.lead_id.in_(lead_ids)
                )
            ).all()
        )

        if follow_up_ids:
            db.query(LeadFollowUpAttempt).filter(
                LeadFollowUpAttempt.follow_up_id.in_(
                    follow_up_ids
                )
            ).delete(synchronize_session=False)

            db.query(LeadFollowUp).filter(
                LeadFollowUp.id.in_(
                    follow_up_ids
                )
            ).delete(synchronize_session=False)

        db.query(Lead).filter(
            Lead.id.in_(lead_ids)
        ).delete(synchronize_session=False)

        db.commit()

    finally:
        db.close()
        _created_lead_ids.clear()


def create_lead() -> int:
    db = SessionLocal()

    try:
        lead = Lead(
            name=f"{TEST_PREFIX}{uuid4().hex}",
            status="new",
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        lead_id = lead.id
        _created_lead_ids.append(lead_id)

        return lead_id

    finally:
        db.close()


def create_follow_up(lead_id: int) -> dict:
    scheduled_at = (
            datetime.now(timezone.utc)
            + timedelta(days=1)
    ).replace(microsecond=0)

    response = client.post(
        "/api/v1/follow-ups",
        json={
            "lead_id": lead_id,
            "scheduled_at": scheduled_at.isoformat(),
        },
    )

    assert response.status_code == 200

    return response.json()


def test_post_creates_and_persists_follow_up():
    lead_id = create_lead()

    created = create_follow_up(lead_id)

    assert created["lead_id"] == lead_id
    assert created["appointment_id"] is None
    assert created["status"] == "PENDING"
    assert created["attempt_count"] == 0
    assert created["completed_at"] is None
    assert len(created["idempotency_key"]) == 64

    db = SessionLocal()

    try:
        persisted = db.get(
            LeadFollowUp,
            created["id"],
        )

        assert persisted is not None
        assert persisted.lead_id == lead_id
        assert persisted.status == "PENDING"
        assert persisted.attempt_count == 0

    finally:
        db.close()


def test_post_is_idempotent():
    lead_id = create_lead()

    scheduled_at = (
            datetime.now(timezone.utc)
            + timedelta(days=1)
    ).replace(microsecond=0)

    payload = {
        "lead_id": lead_id,
        "scheduled_at": scheduled_at.isoformat(),
    }

    first = client.post(
        "/api/v1/follow-ups",
        json=payload,
    )

    second = client.post(
        "/api/v1/follow-ups",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()

    assert first_body["id"] == second_body["id"]
    assert (
            first_body["idempotency_key"]
            == second_body["idempotency_key"]
    )

    db = SessionLocal()

    try:
        follow_ups = list(
            db.scalars(
                select(LeadFollowUp).where(
                    LeadFollowUp.lead_id == lead_id
                )
            ).all()
        )

        assert len(follow_ups) == 1

    finally:
        db.close()


def test_get_returns_persisted_follow_up():
    lead_id = create_lead()

    created = create_follow_up(lead_id)

    response = client.get(
        f"/api/v1/follow-ups/{created['id']}"
    )

    assert response.status_code == 200
    assert response.json() == created


def test_get_rejects_unknown_follow_up():
    response = client.get(
        "/api/v1/follow-ups/999999999"
    )

    assert response.status_code == 404
    assert (
            response.json()["error"]
            == "follow_up_not_found"
    )


def test_cancel_persists_cancelled_status():
    lead_id = create_lead()
    created = create_follow_up(lead_id)

    response = client.post(
        f"/api/v1/follow-ups/{created['id']}/cancel"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "CANCELLED"
    assert body["completed_at"] is None

    db = SessionLocal()

    try:
        persisted = db.get(
            LeadFollowUp,
            created["id"],
        )

        assert persisted is not None
        assert persisted.status == "CANCELLED"
        assert persisted.completed_at is None

    finally:
        db.close()


def test_cancel_is_idempotent():
    lead_id = create_lead()
    created = create_follow_up(lead_id)

    first = client.post(
        f"/api/v1/follow-ups/{created['id']}/cancel"
    )

    second = client.post(
        f"/api/v1/follow-ups/{created['id']}/cancel"
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == "CANCELLED"
    assert second.json()["status"] == "CANCELLED"


def test_failed_attempt_keeps_follow_up_pending():
    lead_id = create_lead()
    created = create_follow_up(lead_id)

    response = client.post(
        f"/api/v1/follow-ups/{created['id']}/attempts",
        json={
            "channel": "MANUAL",
            "status": "FAILED",
            "message": "Lead não respondeu.",
        },
    )

    assert response.status_code == 200

    attempt = response.json()

    assert attempt["follow_up_id"] == created["id"]
    assert attempt["attempt_number"] == 1
    assert attempt["channel"] == "MANUAL"
    assert attempt["status"] == "FAILED"
    assert attempt["message"] == "Lead não respondeu."

    response = client.get(
        f"/api/v1/follow-ups/{created['id']}"
    )

    assert response.status_code == 200

    follow_up = response.json()

    assert follow_up["status"] == "PENDING"
    assert follow_up["attempt_count"] == 1
    assert follow_up["completed_at"] is None


def test_successful_attempt_completes_follow_up():
    lead_id = create_lead()
    created = create_follow_up(lead_id)

    response = client.post(
        f"/api/v1/follow-ups/{created['id']}/attempts",
        json={
            "channel": "MANUAL",
            "status": "SUCCESS",
            "message": "Contato realizado.",
        },
    )

    assert response.status_code == 200

    attempt = response.json()

    assert attempt["attempt_number"] == 1
    assert attempt["status"] == "SUCCESS"

    response = client.get(
        f"/api/v1/follow-ups/{created['id']}"
    )

    assert response.status_code == 200

    follow_up = response.json()

    assert follow_up["status"] == "COMPLETED"
    assert follow_up["attempt_count"] == 1
    assert follow_up["completed_at"] is not None


def test_second_attempt_after_success_is_rejected():
    lead_id = create_lead()
    created = create_follow_up(lead_id)

    first = client.post(
        f"/api/v1/follow-ups/{created['id']}/attempts",
        json={
            "channel": "MANUAL",
            "status": "SUCCESS",
            "message": "Contato realizado.",
        },
    )

    assert first.status_code == 200

    second = client.post(
        f"/api/v1/follow-ups/{created['id']}/attempts",
        json={
            "channel": "MANUAL",
            "status": "FAILED",
            "message": "Nova tentativa indevida.",
        },
    )

    assert second.status_code == 400
    assert (
            second.json()["error"]
            == "follow_up_not_pending"
    )


def test_attempt_on_cancelled_follow_up_is_rejected():
    lead_id = create_lead()
    created = create_follow_up(lead_id)

    cancelled = client.post(
        f"/api/v1/follow-ups/{created['id']}/cancel"
    )

    assert cancelled.status_code == 200

    response = client.post(
        f"/api/v1/follow-ups/{created['id']}/attempts",
        json={
            "channel": "MANUAL",
            "status": "FAILED",
            "message": "Tentativa indevida.",
        },
    )

    assert response.status_code == 400
    assert (
            response.json()["error"]
            == "follow_up_not_pending"
    )


def test_post_rejects_past_schedule():
    lead_id = create_lead()

    scheduled_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
    )

    response = client.post(
        "/api/v1/follow-ups",
        json={
            "lead_id": lead_id,
            "scheduled_at": scheduled_at.isoformat(),
        },
    )

    assert response.status_code == 400
    assert (
            response.json()["error"]
            == "follow_up_in_past"
    )


def test_post_rejects_extra_fields():
    lead_id = create_lead()

    response = client.post(
        "/api/v1/follow-ups",
        json={
            "lead_id": lead_id,
            "scheduled_at": (
                    datetime.now(timezone.utc)
                    + timedelta(days=1)
            ).isoformat(),
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 422


def test_attempt_rejects_invalid_channel():
    response = client.post(
        "/api/v1/follow-ups/1/attempts",
        json={
            "channel": "SMS",
            "status": "FAILED",
        },
    )

    assert response.status_code == 422


def test_attempt_rejects_invalid_status():
    response = client.post(
        "/api/v1/follow-ups/1/attempts",
        json={
            "channel": "MANUAL",
            "status": "PENDING",
        },
    )

    assert response.status_code == 422