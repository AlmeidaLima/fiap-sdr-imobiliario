from app.models.appointment import Appointment


def test_appointment_model_has_expected_columns_and_foreign_keys():
    columns = Appointment.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "lead_id",
        "property_id",
        "appointment_type",
        "scheduled_at",
        "status",
        "idempotency_key",
        "notes",
        "created_at",
        "updated_at",
    }
    assert list(columns["lead_id"].foreign_keys)[0].target_fullname == "leads.id"
    assert list(columns["property_id"].foreign_keys)[0].target_fullname == "properties.id"


def test_appointment_model_constraints_and_nullability():
    columns = Appointment.__table__.columns
    constraint_names = {
        constraint.name for constraint in Appointment.__table__.constraints
    }

    assert columns["lead_id"].nullable is False
    assert columns["property_id"].nullable is True
    assert columns["scheduled_at"].type.timezone is True
    assert columns["idempotency_key"].unique is True
    assert "ck_appointments_type" in constraint_names
    assert "ck_appointments_status" in constraint_names
    assert "ck_appointments_visit_property" in constraint_names
