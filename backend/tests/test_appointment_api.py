from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database.conversation_repository import ConversationRepository
from app.database.lead_repository import LeadRepository
from app.database.property_repository import PropertyRepository
from app.database.session import SessionLocal
from app.main import app
from app.models.appointment import Appointment
from app.models.property import Property


client = TestClient(app)


def create_confirmed_conversation(
        *,
        state_overrides: dict | None = None,
        with_lead: bool = True,
) -> tuple[str, int, int | None]:
    db = SessionLocal()
    token = uuid4().hex
    try:
        property_ = PropertyRepository(db).save(
            Property(
                external_id=f"appointment-property-{token}",
                title="Imóvel para agendamento",
                description="Imóvel fictício de teste.",
                usable_area=70,
                bathrooms=1,
                bedrooms=2,
                parking_spaces=1,
                amenities=[],
                zip_code="80000000",
                neighborhood="Boa Vista",
                pois=[],
                price=Decimal("400000.00"),
                source="test",
                available=True,
            )
        )
        lead_id = None
        if with_lead:
            lead_id = LeadRepository(db).create(name="Lead Appointment").id

        state = {
            "commercial_intent": "COMPRA",
            "neighborhood": "Boa Vista",
            "max_price": "400000",
            "lead_score": 50,
            "lead_classification": "MORNO",
            "accepted_meeting_or_visit": False,
            "presented_property_ids": [property_.id],
            "selected_property_id": property_.id,
            "appointment_stage": "CONFIRMED",
            "appointment_type": "VISITA",
            "appointment_date": "2099-12-31",
            "appointment_time": "14:30:00",
        }
        state.update(state_overrides or {})
        conversation_id = f"appointment-{token}"
        ConversationRepository(db).create(
            conversation_id=conversation_id,
            lead_id=lead_id,
            state=state,
        )
        return conversation_id, property_.id, lead_id
    finally:
        db.close()


def appointment_count(idempotency_key: str) -> int:
    db = SessionLocal()
    try:
        return db.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.idempotency_key == idempotency_key
            )
        )
    finally:
        db.close()


def persisted_state(conversation_id: str) -> dict:
    db = SessionLocal()
    try:
        return ConversationRepository(db).find_by_conversation_id(
            conversation_id
        ).state
    finally:
        db.close()


def test_post_creates_idempotent_appointment_from_persisted_state():
    conversation_id, property_id, lead_id = create_confirmed_conversation()

    first = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    )
    second = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    appointment = first_body["appointment"]
    assert second.json()["appointment"]["id"] == appointment["id"]
    assert appointment["lead_id"] == lead_id
    assert appointment["property_id"] == property_id
    assert appointment["appointment_type"] == "VISITA"
    assert appointment["status"] == "CONFIRMED"
    assert appointment["scheduled_at"] == "2099-12-31T17:30:00Z"
    assert appointment_count(appointment["idempotency_key"]) == 1

    state = persisted_state(conversation_id)
    assert state["appointment_id"] == appointment["id"]
    assert state["appointment_stage"] == "CONFIRMED"
    assert state["lead_score"] == 75
    assert state["lead_classification"] == "QUENTE"
    assert state["accepted_meeting_or_visit"] is True
    assert first_body["state"]["appointment_id"] == appointment["id"]
    assert first_body["state"]["accepted_meeting_or_visit"] is True
    assert first_body["state"]["lead_score"] == 75
    assert first_body["state"]["lead_classification"] == "QUENTE"
    assert second.json()["state"] == first_body["state"]


def test_get_returns_persisted_appointment():
    conversation_id, _, _ = create_confirmed_conversation()
    created = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    ).json()["appointment"]

    response = client.get(f"/api/v1/appointments/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_post_rejects_unknown_conversation():
    response = client.post(
        "/api/v1/appointments",
        json={"conversation_id": f"missing-{uuid4()}"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "conversation_not_found"


def test_post_rejects_conversation_without_lead():
    conversation_id, _, _ = create_confirmed_conversation(with_lead=False)

    response = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "conversation_without_lead"
    state = persisted_state(conversation_id)
    assert state["accepted_meeting_or_visit"] is False
    assert state.get("appointment_id") is None


def test_post_rejects_incomplete_state():
    conversation_id, _, _ = create_confirmed_conversation(
        state_overrides={
            "appointment_stage": "AWAITING_CONFIRMATION",
        }
    )

    response = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "appointment_not_confirmed"
    state = persisted_state(conversation_id)
    assert state["accepted_meeting_or_visit"] is False
    assert state.get("appointment_id") is None


def test_post_rejects_forged_critical_fields():
    conversation_id, _, _ = create_confirmed_conversation()

    response = client.post(
        "/api/v1/appointments",
        json={
            "conversation_id": conversation_id,
            "property_id": 999,
            "lead_id": 999,
            "scheduled_at": "2099-01-01T00:00:00Z",
            "status": "CANCELLED",
        },
    )

    assert response.status_code == 422


def test_appointment_id_survives_next_conversation_turn(monkeypatch):
    conversation_id, _, _ = create_confirmed_conversation()
    created = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    ).json()["appointment"]
    monkeypatch.setattr(
        "app.services.llm_client.LLMClient.chat",
        lambda self, messages: (_ for _ in ()).throw(
            AssertionError("O LLM não deve participar do agendamento.")
        ),
    )

    response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "confirmo novamente",
        },
    )

    assert response.status_code == 200
    assert response.json()["state"]["appointment_id"] == created["id"]
    assert response.json()["state"]["accepted_meeting_or_visit"] is True
    assert response.json()["state"]["lead_score"] == 75
    assert response.json()["state"]["lead_classification"] == "QUENTE"


def test_appointment_commercial_effect_respects_score_cap():
    conversation_id, _, _ = create_confirmed_conversation(
        state_overrides={
            "urgency_days": 30,
            "lead_score": 75,
            "lead_classification": "QUENTE",
        }
    )

    response = client.post(
        "/api/v1/appointments",
        json={"conversation_id": conversation_id},
    )

    assert response.status_code == 200
    state = persisted_state(conversation_id)
    assert state["accepted_meeting_or_visit"] is True
    assert state["lead_score"] == 100
    assert state["lead_classification"] == "QUENTE"
