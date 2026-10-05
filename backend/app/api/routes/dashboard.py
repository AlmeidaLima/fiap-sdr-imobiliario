from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.appointment_repository import AppointmentRepository
from app.database.conversation_repository import ConversationRepository
from app.database.dashboard_repository import DashboardRepository
from app.database.lead_repository import LeadRepository
from app.database.property_repository import PropertyRepository
from app.database.session import get_db
from app.schemas.dashboard import (
    DashboardLeadDetailResponse,
    DashboardLeadListResponse,
)
from app.services.dashboard_service import DashboardService
from app.services.lead_handoff_service import LeadHandoffService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def _dashboard_service(db: Session) -> DashboardService:
    property_repository = PropertyRepository(db)
    appointment_repository = AppointmentRepository(db)
    lead_handoff_service = LeadHandoffService(
        conversation_repository=ConversationRepository(db),
        lead_repository=LeadRepository(db),
        property_repository=property_repository,
        appointment_repository=appointment_repository,
    )
    return DashboardService(
        dashboard_repository=DashboardRepository(db),
        property_repository=property_repository,
        appointment_repository=appointment_repository,
        lead_handoff_service=lead_handoff_service,
    )


@router.get("/leads", response_model=DashboardLeadListResponse)
def list_dashboard_leads(
        db: Session = Depends(get_db),
) -> DashboardLeadListResponse:
    return _dashboard_service(db).list_leads()


@router.get(
    "/leads/{lead_id}",
    response_model=DashboardLeadDetailResponse,
)
def get_dashboard_lead(
        lead_id: int,
        db: Session = Depends(get_db),
) -> DashboardLeadDetailResponse:
    return _dashboard_service(db).get_lead_detail(lead_id)
