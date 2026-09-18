from app.models.conversation import Conversation
from app.models.lead import Lead  # noqa: F401
from app.models.message import Message


def test_message_model_table_name():
    assert Message.__tablename__ == "messages"


def test_message_model_has_expected_columns():
    columns = Message.__table__.columns

    assert "id" in columns
    assert "conversation_id" in columns
    assert "role" in columns
    assert "content" in columns
    assert "created_at" in columns


def test_message_model_required_columns():
    columns = Message.__table__.columns

    assert columns["id"].primary_key is True
    assert columns["conversation_id"].nullable is False
    assert columns["role"].nullable is False
    assert columns["content"].nullable is False
    assert columns["created_at"].nullable is False


def test_message_model_has_conversation_foreign_key():
    conversation_id = Message.__table__.columns["conversation_id"]

    foreign_keys = list(conversation_id.foreign_keys)

    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "conversations.id"