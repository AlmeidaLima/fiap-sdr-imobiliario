from datetime import datetime, timezone
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dashboard import (
    DashboardLeadDetailResponse,
    DashboardLeadListResponse,
    DashboardLeadSummary,
    DashboardPreferences,
)
from app.schemas.lead_handoff import (
    LeadHandoffQualification,
    LeadHandoffResponse,
)


client = TestClient(app)
NOW = datetime(2026, 10, 5, 14, 30, tzinfo=timezone.utc)


def lead_summary() -> DashboardLeadSummary:
    return DashboardLeadSummary(
        lead_id=1,
        conversation_id="conversation-1",
        name="Rafael",
        status="new",
        commercial_intent="COMPRA",
        score=75,
        classification="QUENTE",
        last_interaction_at=NOW,
    )


def detail() -> DashboardLeadDetailResponse:
    return DashboardLeadDetailResponse(
        lead=lead_summary(),
        preferences=DashboardPreferences(
            urgency_days=None,
            neighborhood=None,
            min_price=None,
            max_price=None,
            min_bedrooms=None,
            min_bathrooms=None,
            min_parking_spaces=None,
            min_usable_area=None,
            semantic_preferences=[],
        ),
        history=[],
        recommended_properties=[],
        selected_property=None,
        summary=LeadHandoffResponse(
            conversation_id="conversation-1",
            handoff_status="NOT_READY",
            lead=None,
            qualification=LeadHandoffQualification(
                commercial_intent=None,
                urgency_days=None,
                neighborhood=None,
                min_price=None,
                max_price=None,
                min_bedrooms=None,
                min_bathrooms=None,
                min_parking_spaces=None,
                min_usable_area=None,
            ),
            property=None,
            appointment=None,
        ),
        appointments=[],
    )


def test_list_endpoint_returns_contract(monkeypatch):
    list_leads = Mock(
        return_value=DashboardLeadListResponse(leads=[lead_summary()]),
    )
    monkeypatch.setattr(
        "app.api.routes.dashboard.DashboardService.list_leads",
        list_leads,
    )

    response = client.get("/api/v1/dashboard/leads")

    assert response.status_code == 200
    body = response.json()
    assert body["leads"][0]["lead_id"] == 1
    assert body["leads"][0]["last_interaction_at"] == "2026-10-05T14:30:00Z"
    list_leads.assert_called_once_with()


def test_list_endpoint_returns_empty_list(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.dashboard.DashboardService.list_leads",
        Mock(return_value=DashboardLeadListResponse(leads=[])),
    )

    response = client.get("/api/v1/dashboard/leads")

    assert response.status_code == 200
    assert response.json() == {"leads": []}


def test_detail_endpoint_returns_contract_without_internal_fields(monkeypatch):
    get_lead_detail = Mock(return_value=detail())
    monkeypatch.setattr(
        "app.api.routes.dashboard.DashboardService.get_lead_detail",
        get_lead_detail,
    )

    response = client.get("/api/v1/dashboard/leads/1")

    assert response.status_code == 200
    body = response.json()
    assert body["lead"]["lead_id"] == 1
    assert body["history"] == []
    assert body["recommended_properties"] == []
    assert body["appointments"] == []
    assert "state" not in body
    assert "idempotency_key" not in response.text
    get_lead_detail.assert_called_once_with(1)


def test_detail_endpoint_rejects_invalid_lead_id():
    response = client.get("/api/v1/dashboard/leads/not-a-number")

    assert response.status_code == 422


def test_detail_endpoint_returns_standard_error_for_unknown_lead():
    response = client.get("/api/v1/dashboard/leads/2147483647")

    assert response.status_code == 404
    assert response.json()["error"] == "lead_not_found"
