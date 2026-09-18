from app.models.lead import Lead


def test_lead_model_table_name():
    assert Lead.__tablename__ == "leads"


def test_lead_model_has_expected_columns():
    columns = Lead.__table__.columns

    assert "id" in columns
    assert "name" in columns
    assert "phone" in columns
    assert "email" in columns
    assert "status" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


def test_lead_model_required_columns():
    columns = Lead.__table__.columns

    assert columns["id"].primary_key is True

    assert columns["name"].nullable is True
    assert columns["phone"].nullable is True
    assert columns["email"].nullable is True

    assert columns["status"].nullable is False
    assert columns["created_at"].nullable is False
    assert columns["updated_at"].nullable is False