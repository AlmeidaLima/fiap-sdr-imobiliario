from app.models.conversation import Conversation


def test_conversation_model_table_name():
    assert Conversation.__tablename__ == "conversations"


def test_conversation_model_has_expected_columns():
    columns = Conversation.__table__.columns

    assert "id" in columns
    assert "conversation_id" in columns
    assert "lead_id" in columns
    assert "status" in columns
    assert "state" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


def test_conversation_model_required_columns():
    columns = Conversation.__table__.columns

    assert columns["id"].primary_key is True
    assert columns["conversation_id"].nullable is False
    assert columns["lead_id"].nullable is True
    assert columns["status"].nullable is False
    assert columns["state"].nullable is False
    assert columns["created_at"].nullable is False
    assert columns["updated_at"].nullable is False


def test_conversation_model_has_lead_foreign_key():
    lead_id = Conversation.__table__.columns["lead_id"]

    foreign_keys = list(lead_id.foreign_keys)

    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "leads.id"


def test_conversation_id_is_unique():
    conversation_id = Conversation.__table__.columns["conversation_id"]

    assert conversation_id.unique is True