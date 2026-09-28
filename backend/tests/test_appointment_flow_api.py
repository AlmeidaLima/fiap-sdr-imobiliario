from uuid import uuid4

from fastapi.testclient import TestClient

from app.database.conversation_repository import ConversationRepository
from app.database.session import SessionLocal
from app.main import app


client = TestClient(app)


def test_appointment_flow_is_persisted_without_search_or_llm(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.conversations.EmbeddingService",
        lambda: (_ for _ in ()).throw(
            AssertionError("A busca não deveria ser inicializada.")
        ),
    )
    monkeypatch.setattr(
        "app.services.llm_client.LLMClient.chat",
        lambda self, messages: (_ for _ in ()).throw(
            AssertionError("O LLM não deveria ser chamado.")
        ),
    )
    conversation_id = f"appointment-api-{uuid4()}"
    db = SessionLocal()
    try:
        ConversationRepository(db).create(
            conversation_id=conversation_id,
            state={
                "commercial_intent": "COMPRA",
                "neighborhood": "Boa Vista",
                "max_price": "700000",
                "min_bedrooms": 3,
                "lead_score": 50,
                "lead_classification": "MORNO",
                "presented_property_ids": [10, 20],
            },
        )
    finally:
        db.close()

    turns = [
        ({"message": "Tenho interesse neste imóvel.", "selected_property_id": 10}, "AWAITING_TYPE"),
        ({"message": "Quero marcar uma visita"}, "AWAITING_DATE"),
        ({"message": "31/12/2099"}, "AWAITING_TIME"),
        ({"message": "14h30"}, "AWAITING_CONFIRMATION"),
        ({"message": "confirmo"}, "CONFIRMED"),
    ]

    for payload, expected_stage in turns:
        response = client.post(
            "/api/v1/conversations/turn",
            json={"conversation_id": conversation_id, **payload},
        )

        assert response.status_code == 200
        state = response.json()["state"]
        assert state["appointment_stage"] == expected_stage
        assert state["presented_property_ids"] == [10, 20]
        assert state["selected_property_id"] == 10
        assert state["accepted_meeting_or_visit"] is False
        assert state["lead_score"] == 50
        assert response.json()["properties"] == []

    assert state["appointment_type"] == "VISITA"
    assert state["appointment_date"] == "2099-12-31"
    assert state["appointment_time"] == "14:30:00"

    db = SessionLocal()
    try:
        persisted = ConversationRepository(db).find_by_conversation_id(
            conversation_id,
        )
        assert persisted.state["appointment_stage"] == "CONFIRMED"
        assert persisted.state["accepted_meeting_or_visit"] is False
    finally:
        db.close()
