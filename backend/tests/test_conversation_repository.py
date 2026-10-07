from uuid import uuid4

from app.database.conversation_repository import ConversationRepository
from datetime import datetime, timedelta
from app.models.message import Message
from app.database.lead_repository import LeadRepository
from app.database.session import SessionLocal


def test_create_and_find_conversation():
    db = SessionLocal()

    try:
        repository = ConversationRepository(db)

        conversation_id = f"test-{uuid4()}"

        created = repository.create(
            conversation_id=conversation_id,
            state={
                "neighborhood": "Boa Vista",
            },
        )

        found = repository.find_by_conversation_id(
            conversation_id
        )

        assert created.id is not None
        assert found is not None
        assert found.id == created.id
        assert found.conversation_id == conversation_id
        assert found.status == "active"
        assert found.state["neighborhood"] == "Boa Vista"

    finally:
        db.close()


def test_find_latest_by_lead_uses_interaction_update_and_id_priority():
    db = SessionLocal()
    try:
        repository = ConversationRepository(db)
        lead = LeadRepository(db).create(name="Latest conversation")
        base = datetime(2026, 10, 5, 10, 0)
        older = repository.create(
            conversation_id=f"test-{uuid4()}",
            lead_id=lead.id,
        )
        newer = repository.create(
            conversation_id=f"test-{uuid4()}",
            lead_id=lead.id,
        )
        older.updated_at = base + timedelta(days=1)
        newer.updated_at = base
        db.add_all([
            Message(
                conversation_id=older.id,
                role="user",
                content="Older",
                created_at=base,
            ),
            Message(
                conversation_id=newer.id,
                role="assistant",
                content="Newer",
                created_at=base + timedelta(hours=1),
            ),
        ])
        db.commit()

        assert repository.find_latest_by_lead_id(lead.id).id == newer.id

        db.query(Message).filter(
            Message.conversation_id.in_([older.id, newer.id])
        ).delete(synchronize_session=False)
        newer.updated_at = older.updated_at
        db.commit()
        assert repository.find_latest_by_lead_id(lead.id).id == newer.id
    finally:
        db.close()


def test_find_latest_by_lead_returns_none_without_conversation():
    db = SessionLocal()
    try:
        lead = LeadRepository(db).create(name="No conversation")
        assert ConversationRepository(db).find_latest_by_lead_id(lead.id) is None
    finally:
        db.close()


def test_update_conversation_state():
    db = SessionLocal()

    try:
        repository = ConversationRepository(db)

        conversation_id = f"test-{uuid4()}"

        conversation = repository.create(
            conversation_id=conversation_id,
            state={
                "neighborhood": "Boa Vista",
            },
        )

        updated = repository.update_state(
            conversation=conversation,
            state={
                "neighborhood": "Boa Vista",
                "max_price": "700000",
                "min_bedrooms": 3,
            },
        )

        found = repository.find_by_conversation_id(
            conversation_id
        )

        assert updated.state["max_price"] == "700000"

        assert found is not None
        assert found.state["neighborhood"] == "Boa Vista"
        assert found.state["max_price"] == "700000"
        assert found.state["min_bedrooms"] == 3

    finally:
        db.close()


def test_associate_lead_to_conversation():
    db = SessionLocal()

    try:
        conversation_repository = ConversationRepository(db)
        lead_repository = LeadRepository(db)

        lead = lead_repository.create(
            name="Lead Teste",
            phone="61999999999",
            email="lead.teste@example.com",
        )

        conversation = conversation_repository.create(
            conversation_id=f"test-{uuid4()}",
            state={},
        )

        updated = conversation_repository.associate_lead(
            conversation=conversation,
            lead_id=lead.id,
        )

        found = (
            conversation_repository.find_by_conversation_id(
                conversation.conversation_id
            )
        )

        assert updated.lead_id == lead.id

        assert found is not None
        assert found.lead_id == lead.id

    finally:
        db.close()
