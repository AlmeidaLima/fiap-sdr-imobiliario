from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.core.exceptions import ApplicationException
from app.database.dashboard_repository import DashboardLeadRecord
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.models.property import Property
from app.schemas.lead_handoff import (
    LeadHandoffLead,
    LeadHandoffQualification,
    LeadHandoffResponse,
)
from app.services.dashboard_service import DashboardService


NOW = datetime(2026, 10, 5, 14, 30, tzinfo=timezone.utc)


def property_(property_id: int, title: str) -> Property:
    return Property(
        id=property_id,
        external_id=f"property-{property_id}",
        title=title,
        description="Descrição",
        usable_area=70,
        bathrooms=2,
        bedrooms=3,
        parking_spaces=1,
        amenities=[],
        zip_code="80000000",
        neighborhood="Boa Vista",
        pois=[],
        price=Decimal("350000.00"),
        source="test",
        available=True,
    )


def handoff(status: str = "NOT_READY") -> LeadHandoffResponse:
    return LeadHandoffResponse(
        conversation_id="conversation-1",
        handoff_status=status,
        lead=LeadHandoffLead(
            id=1, name=None, score=75, classification="QUENTE",
        ),
        qualification=LeadHandoffQualification(
            commercial_intent="COMPRA",
            urgency_days=30,
            neighborhood="Boa Vista",
            min_price=None,
            max_price=Decimal("400000"),
            min_bedrooms=3,
            min_bathrooms=None,
            min_parking_spaces=None,
            min_usable_area=None,
        ),
        property=None,
        appointment=None,
    )


def build_service(state: dict | None = None):
    lead = Lead(id=1, name=None, status="custom-status")
    conversation = Conversation(
        id=10,
        conversation_id="conversation-1",
        lead_id=1,
        state=state or {},
    )
    record = DashboardLeadRecord(
        lead=lead,
        conversation=conversation,
        last_interaction_at=NOW,
    )
    dashboard_repository = Mock()
    dashboard_repository.get_lead.return_value = lead
    dashboard_repository.get_lead_record.return_value = record
    dashboard_repository.list_leads.return_value = [record]
    dashboard_repository.list_public_messages.return_value = []
    property_repository = Mock()
    property_repository.find_by_ids.return_value = []
    property_repository.find_by_id.return_value = None
    appointment_repository = Mock()
    appointment_repository.list_by_lead_id.return_value = []
    handoff_service = Mock()
    handoff_service.get_by_conversation_id.return_value = handoff()
    service = DashboardService(
        dashboard_repository=dashboard_repository,
        property_repository=property_repository,
        appointment_repository=appointment_repository,
        lead_handoff_service=handoff_service,
    )
    return (
        service,
        dashboard_repository,
        property_repository,
        appointment_repository,
        handoff_service,
    )


def test_list_leads_uses_persisted_status_and_partial_state_defaults():
    service, *_ = build_service()

    result = service.list_leads()

    assert result.leads[0].status == "custom-status"
    assert result.leads[0].commercial_intent is None
    assert result.leads[0].score == 0
    assert result.leads[0].classification == "FRIO"


def test_list_leads_returns_empty_collection():
    service, repository, *_ = build_service()
    repository.list_leads.return_value = []

    assert service.list_leads().leads == []


def test_detail_composes_preferences_history_properties_and_appointments():
    state = {
        "commercial_intent": "COMPRA",
        "lead_score": 75,
        "lead_classification": "QUENTE",
        "urgency_days": 30,
        "neighborhood": "Boa Vista",
        "max_price": "400000",
        "min_bedrooms": 3,
        "semantic_preferences": ["varanda"],
        "presented_property_ids": [20, 999, 10],
        "selected_property_id": 10,
    }
    service, dashboard, properties, appointments, handoffs = build_service(state)
    recommended = [property_(20, "Primeiro"), property_(10, "Segundo")]
    selected = recommended[1]
    properties.find_by_ids.return_value = recommended
    properties.find_by_id.return_value = selected
    dashboard.list_public_messages.return_value = [
        Message(id=1, conversation_id=10, role="user", content="Olá", created_at=NOW),
        Message(id=2, conversation_id=10, role="assistant", content="Olá!", created_at=NOW),
    ]
    appointment = Appointment(
        id=30,
        lead_id=1,
        property_id=10,
        appointment_type="VISITA",
        scheduled_at=NOW,
        status="CONFIRMED",
        idempotency_key="must-not-be-projected",
        notes=None,
        created_at=NOW,
        updated_at=NOW,
    )
    appointments.list_by_lead_id.return_value = [appointment]
    handoffs.get_by_conversation_id.return_value = handoff("NOT_READY")

    result = service.get_lead_detail(1)

    assert result.lead.score == 75
    assert result.preferences.neighborhood == "Boa Vista"
    assert result.preferences.semantic_preferences == ["varanda"]
    assert [message.role for message in result.history] == ["user", "assistant"]
    assert [item.id for item in result.recommended_properties] == [20, 10]
    assert result.selected_property.id == 10
    assert result.summary.handoff_status == "NOT_READY"
    assert result.appointments[0].id == 30
    assert "idempotency_key" not in result.appointments[0].model_dump()
    properties.find_by_ids.assert_called_once_with([20, 999, 10])
    handoffs.get_by_conversation_id.assert_called_once_with("conversation-1")


def test_detail_supports_ready_handoff():
    service, *_, handoffs = build_service()
    handoffs.get_by_conversation_id.return_value = handoff("READY")

    result = service.get_lead_detail(1)

    assert result.summary.handoff_status == "READY"


def test_invalid_persisted_state_does_not_use_commercial_defaults():
    invalid_state = {
        "commercial_intent": "VENDA",
        "lead_score": 55,
        "lead_classification": "MORNO",
    }
    service, dashboard, properties, appointments, handoffs = build_service(
        invalid_state,
    )

    with pytest.raises(ValidationError):
        service.get_lead_detail(1)

    assert dashboard.get_lead_record.return_value.conversation.state == (
        invalid_state
    )
    properties.find_by_ids.assert_not_called()
    appointments.list_by_lead_id.assert_not_called()
    handoffs.get_by_conversation_id.assert_not_called()


@pytest.mark.parametrize("lead_exists", [False, True])
def test_missing_lead_or_conversation_returns_not_found(lead_exists: bool):
    service, repository, *_ = build_service()
    if not lead_exists:
        repository.get_lead.return_value = None
    else:
        repository.get_lead_record.return_value = None

    with pytest.raises(ApplicationException) as error:
        service.get_lead_detail(1)

    assert error.value.status_code == 404
    assert error.value.error == "lead_not_found"
