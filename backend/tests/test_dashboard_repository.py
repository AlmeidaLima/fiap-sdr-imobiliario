from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.dashboard_repository import DashboardRepository
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lead.__table__.create(engine)
    Conversation.__table__.create(engine)
    Message.__table__.create(engine)
    with Session(engine) as session:
        yield session


def add_lead(db: Session, name: str, status: str = "new") -> Lead:
    lead = Lead(name=name, status=status)
    db.add(lead)
    db.flush()
    return lead


def add_conversation(
        db: Session,
        lead: Lead | None,
        conversation_id: str,
        updated_at: datetime,
        state: dict | None = None,
) -> Conversation:
    conversation = Conversation(
        conversation_id=conversation_id,
        lead_id=lead.id if lead else None,
        state=state or {},
        updated_at=updated_at,
    )
    db.add(conversation)
    db.flush()
    return conversation


def add_message(
        db: Session,
        conversation: Conversation,
        role: str,
        content: str,
        created_at: datetime,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        created_at=created_at,
    )
    db.add(message)
    db.flush()
    return message


def test_list_leads_returns_empty_list(db: Session):
    assert DashboardRepository(db).list_leads() == []


def test_list_leads_uses_latest_interaction_and_orders_null_last(db: Session):
    base = datetime(2026, 10, 5, 10, 0)
    first_lead = add_lead(db, "Primeiro")
    second_lead = add_lead(db, "Segundo")
    without_message = add_lead(db, "Sem mensagem")
    first_conversation = add_conversation(
        db, first_lead, "first", base,
    )
    second_conversation = add_conversation(
        db, second_lead, "second", base,
    )
    add_conversation(db, without_message, "without", base)
    add_message(db, first_conversation, "user", "Anterior", base)
    latest = add_message(
        db,
        second_conversation,
        "assistant",
        "Mais recente",
        base + timedelta(hours=1),
    )
    db.commit()

    records = DashboardRepository(db).list_leads()

    assert [record.lead.name for record in records] == [
        "Segundo", "Primeiro", "Sem mensagem",
    ]
    assert records[0].last_interaction_at == latest.created_at
    assert records[2].last_interaction_at is None


def test_selects_latest_conversation_by_approved_priority(db: Session):
    base = datetime(2026, 10, 5, 10, 0)
    lead = add_lead(db, "Lead")
    older_conversation = add_conversation(
        db, lead, "older-conversation", base + timedelta(days=2),
    )
    newer_interaction = add_conversation(
        db, lead, "newer-interaction", base,
    )
    add_message(
        db, older_conversation, "user", "Antiga", base,
    )
    add_message(
        db, newer_interaction, "assistant", "Nova", base + timedelta(hours=1),
    )
    db.commit()

    record = DashboardRepository(db).get_lead_record(lead.id)

    assert record is not None
    assert record.conversation.conversation_id == "newer-interaction"


def test_list_returns_one_row_for_lead_with_multiple_conversations(db: Session):
    base = datetime(2026, 10, 5, 10, 0)
    lead = add_lead(db, "Lead com duas conversas")
    first = add_conversation(db, lead, "first-conversation", base)
    second = add_conversation(db, lead, "second-conversation", base)
    add_message(db, first, "user", "Primeira", base)
    add_message(
        db, second, "assistant", "Segunda", base + timedelta(minutes=1),
    )
    db.commit()

    records = DashboardRepository(db).list_leads()

    assert len(records) == 1
    assert records[0].lead.id == lead.id
    assert records[0].conversation.id == second.id


def test_list_omits_lead_without_conversation(db: Session):
    lead_without_conversation = add_lead(db, "Sem conversa")
    lead_with_conversation = add_lead(db, "Com conversa")
    add_conversation(
        db,
        lead_with_conversation,
        "usable-conversation",
        datetime(2026, 10, 5, 10, 0),
    )
    db.commit()

    records = DashboardRepository(db).list_leads()

    assert [record.lead.id for record in records] == [lead_with_conversation.id]
    assert lead_without_conversation.id not in {
        record.lead.id for record in records
    }


def test_equal_last_interaction_uses_updated_at_then_conversation_id(
        db: Session,
):
    base = datetime(2026, 10, 5, 10, 0)
    lead = add_lead(db, "Lead empatado")
    old_update = add_conversation(db, lead, "old-update", base)
    same_update_first = add_conversation(
        db, lead, "same-update-first", base + timedelta(hours=1),
    )
    same_update_higher_id = add_conversation(
        db, lead, "same-update-higher-id", base + timedelta(hours=1),
    )
    for conversation in (old_update, same_update_first, same_update_higher_id):
        add_message(db, conversation, "user", "Mesmo horário", base)
    db.commit()

    records = DashboardRepository(db).list_leads()

    assert len(records) == 1
    assert records[0].conversation.id == same_update_higher_id.id
    assert same_update_higher_id.id > same_update_first.id


def test_conversation_tie_uses_updated_at_then_id(db: Session):
    base = datetime(2026, 10, 5, 10, 0)
    lead = add_lead(db, "Lead")
    add_conversation(db, lead, "old-update", base)
    recent_update = add_conversation(
        db, lead, "recent-update", base + timedelta(hours=1),
    )
    same_update_higher_id = add_conversation(
        db, lead, "higher-id", base + timedelta(hours=1),
    )
    db.commit()

    record = DashboardRepository(db).get_lead_record(lead.id)

    assert record is not None
    assert record.conversation.id == same_update_higher_id.id
    assert record.conversation.id > recent_update.id


def test_public_history_filters_internal_roles_and_orders_chronologically(
        db: Session,
):
    base = datetime(2026, 10, 5, 10, 0)
    lead = add_lead(db, "Lead")
    conversation = add_conversation(db, lead, "history", base)
    assistant = add_message(
        db, conversation, "assistant", "Resposta", base + timedelta(minutes=2),
    )
    user = add_message(db, conversation, "user", "Pergunta", base)
    add_message(db, conversation, "system", "Prompt interno", base)
    add_message(db, conversation, "tool", "Payload interno", base)
    db.commit()

    messages = DashboardRepository(db).list_public_messages(conversation.id)

    assert [message.id for message in messages] == [user.id, assistant.id]
    assert [message.role for message in messages] == ["user", "assistant"]
