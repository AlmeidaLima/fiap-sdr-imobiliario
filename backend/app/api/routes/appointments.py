from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.appointment_repository import AppointmentRepository
from app.database.conversation_repository import ConversationRepository
from app.database.property_repository import PropertyRepository
from app.database.session import get_db
from app.schemas.appointment import (
    AppointmentCreateResponse,
    AppointmentCreateRequest,
    AppointmentResponse,
)
from app.services.appointment_service import AppointmentService


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)


def _appointment_service(db: Session) -> AppointmentService:
    return AppointmentService(
        appointment_repository=AppointmentRepository(db),
        conversation_repository=ConversationRepository(db),
        property_repository=PropertyRepository(db),
        business_timezone=settings.business_timezone,
    )


@router.post("", response_model=AppointmentCreateResponse)
def create_appointment(
        request: AppointmentCreateRequest,
        db: Session = Depends(get_db),
) -> AppointmentCreateResponse:
    appointment, state = (
        _appointment_service(db).create_from_conversation_with_state(
            request.conversation_id
        )
    )
    return AppointmentCreateResponse(
        appointment=AppointmentResponse.model_validate(appointment),
        state=state,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
        appointment_id: int,
        db: Session = Depends(get_db),
) -> AppointmentResponse:
    appointment = _appointment_service(db).get_by_id(appointment_id)
    return AppointmentResponse.model_validate(appointment)
