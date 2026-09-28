from sqlalchemy import inspect

from app.database.session import engine


def test_appointments_table_has_expected_database_constraints():
    inspector = inspect(engine)

    assert "appointments" in inspector.get_table_names()
    columns = {
        column["name"]: column
        for column in inspector.get_columns("appointments")
    }
    foreign_keys = inspector.get_foreign_keys("appointments")
    unique_constraints = inspector.get_unique_constraints("appointments")

    assert columns["lead_id"]["nullable"] is False
    assert columns["property_id"]["nullable"] is True
    assert columns["scheduled_at"]["type"].timezone is True
    assert {foreign_key["referred_table"] for foreign_key in foreign_keys} == {
        "leads",
        "properties",
    }
    assert any(
        constraint["column_names"] == ["idempotency_key"]
        for constraint in unique_constraints
    )
