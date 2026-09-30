from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.appointment_repository import AppointmentRepository
from app.database.conversation_repository import ConversationRepository
from app.database.lead_repository import LeadRepository
from app.database.property_repository import PropertyRepository
from app.database.session import get_db
from app.schemas.lead_handoff import LeadHandoffResponse
from app.services.lead_handoff_service import LeadHandoffService


router = APIRouter(
    prefix="/handoffs",
    tags=["Handoffs"],
)


def _lead_handoff_service(db: Session) -> LeadHandoffService:
    return LeadHandoffService(
        conversation_repository=ConversationRepository(db),
        lead_repository=LeadRepository(db),
        property_repository=PropertyRepository(db),
        appointment_repository=AppointmentRepository(db),
    )


@router.get(
    "/{conversation_id}",
    response_model=LeadHandoffResponse,
)
def get_lead_handoff(
        conversation_id: str,
        db: Session = Depends(get_db),
) -> LeadHandoffResponse:
    return _lead_handoff_service(db).get_by_conversation_id(
        conversation_id
    )
