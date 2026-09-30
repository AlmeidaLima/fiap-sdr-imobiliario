from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
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
SCHEDULED_AT = datetime(2099, 12, 31, 17, 30, tzinfo=timezone.utc)


def create_property(db, token: str) -> Property:
    return PropertyRepository(db).save(
        Property(
            external_id=f"handoff-property-{token}",
            title="Apartamento canônico",
            description="Imóvel fictício para teste de handoff.",
            usable_area=73,
            bathrooms=2,
            bedrooms=3,
            parking_spaces=1,
            amenities=[],
            zip_code="80000000",
            neighborhood="Boa Vista",
            pois=[],
            price=Decimal("279990.45"),
            source="test",
            available=True,
        )
    )


def create_handoff_data(
        *,
        with_appointment: bool = True,
        appointment_type: str = "VISITA",
        appointment_property: bool = True,
        missing_appointment: bool = False,
) -> tuple[str, int | None, dict]:
    db = SessionLocal()
    token = uuid4().hex
    try:
        lead = LeadRepository(db).create(name="Rafael Canônico")
        property_ = create_property(db, token)
        appointment = None
        if with_appointment and not missing_appointment:
            appointment = Appointment(
                lead_id=lead.id,
                property_id=(property_.id if appointment_property else None),
                appointment_type=appointment_type,
                scheduled_at=SCHEDULED_AT,
                status="CONFIRMED",
                idempotency_key=f"handoff-{token}",
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)

        appointment_id = (
            2_000_000_000
            if missing_appointment
            else appointment.id if appointment is not None else None
        )
        state = {
            "lead_name": "Nome não canônico",
            "commercial_intent": "COMPRA",
            "urgency_days": 30,
            "accepted_meeting_or_visit": True,
            "lead_score": 100,
            "lead_classification": "QUENTE",
            "neighborhood": "Boa Vista",
            "min_price": "250000.10",
            "max_price": "400000.99",
            "min_bedrooms": 3,
            "min_bathrooms": 2,
            "min_parking_spaces": 1,
            "min_usable_area": 70,
            "selected_property_id": (
                property_.id if appointment_property else None
            ),
            "appointment_stage": "CONFIRMED",
            "appointment_type": "REUNIAO",
            "appointment_date": "2030-01-01",
            "appointment_time": "09:15:00",
            "appointment_id": appointment_id,
        }
        conversation_id = f"handoff-{token}"
        ConversationRepository(db).create(
            conversation_id=conversation_id,
            lead_id=lead.id,
            state=state,
        )
        return conversation_id, appointment_id, deepcopy(state)
    finally:
        db.close()


def persisted_state(conversation_id: str) -> dict:
    db = SessionLocal()
    try:
        conversation = ConversationRepository(db).find_by_conversation_id(
            conversation_id
        )
        return deepcopy(conversation.state)
    finally:
        db.close()


def appointment_count(appointment_id: int) -> int:
    db = SessionLocal()
    try:
        return db.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.id == appointment_id
            )
        )
    finally:
        db.close()


def test_get_unknown_conversation_returns_standard_not_found_error():
    response = client.get(f"/api/v1/handoffs/missing-{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"] == "conversation_not_found"


def test_get_conversation_without_appointment_returns_not_ready():
    conversation_id, _, _ = create_handoff_data(with_appointment=False)

    response = client.get(f"/api/v1/handoffs/{conversation_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["handoff_status"] == "NOT_READY"
    assert body["property"] is None
    assert body["appointment"] is None
    assert body["qualification"]["neighborhood"] == "Boa Vista"


def test_get_missing_appointment_returns_not_ready():
    conversation_id, _, _ = create_handoff_data(missing_appointment=True)

    response = client.get(f"/api/v1/handoffs/{conversation_id}")

    assert response.status_code == 200
    assert response.json()["handoff_status"] == "NOT_READY"


def test_get_valid_visit_returns_canonical_ready_projection():
    conversation_id, appointment_id, _ = create_handoff_data()

    response = client.get(f"/api/v1/handoffs/{conversation_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == conversation_id
    assert body["handoff_status"] == "READY"
    assert body["lead"]["name"] == "Rafael Canônico"
    assert body["lead"]["score"] == 100
    assert body["lead"]["classification"] == "QUENTE"
    assert body["qualification"]["min_price"] == "250000.10"
    assert body["qualification"]["max_price"] == "400000.99"
    assert body["property"]["title"] == "Apartamento canônico"
    assert body["property"]["price"] == "279990.45"
    assert body["property"]["bedrooms"] == 3
    assert body["appointment"] == {
        "id": appointment_id,
        "appointment_type": "VISITA",
        "scheduled_at": "2099-12-31T17:30:00Z",
        "status": "CONFIRMED",
    }


def test_get_valid_meeting_without_property_returns_null_property():
    conversation_id, appointment_id, _ = create_handoff_data(
        appointment_type="REUNIAO",
        appointment_property=False,
    )

    response = client.get(f"/api/v1/handoffs/{conversation_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["handoff_status"] == "READY"
    assert body["property"] is None
    assert body["appointment"]["id"] == appointment_id
    assert body["appointment"]["appointment_type"] == "REUNIAO"


def test_repeated_get_is_equivalent_and_has_no_side_effects():
    conversation_id, appointment_id, original_state = create_handoff_data()
    count_before = appointment_count(appointment_id)

    first = client.get(f"/api/v1/handoffs/{conversation_id}")
    second = client.get(f"/api/v1/handoffs/{conversation_id}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert persisted_state(conversation_id) == original_state
    assert appointment_count(appointment_id) == count_before == 1


def test_route_delegates_projection_to_lead_handoff_service(monkeypatch):
    expected = {
        "conversation_id": "delegated-conversation",
        "handoff_status": "NOT_READY",
        "lead": None,
        "qualification": {
            "commercial_intent": None,
            "urgency_days": None,
            "neighborhood": None,
            "min_price": None,
            "max_price": None,
            "min_bedrooms": None,
            "min_bathrooms": None,
            "min_parking_spaces": None,
            "min_usable_area": None,
        },
        "property": None,
        "appointment": None,
    }
    get_by_conversation_id = Mock(return_value=expected)
    monkeypatch.setattr(
        "app.api.routes.handoffs.LeadHandoffService.get_by_conversation_id",
        get_by_conversation_id,
    )

    response = client.get("/api/v1/handoffs/delegated-conversation")

    assert response.status_code == 200
    assert response.json() == expected
    get_by_conversation_id.assert_called_once_with("delegated-conversation")
