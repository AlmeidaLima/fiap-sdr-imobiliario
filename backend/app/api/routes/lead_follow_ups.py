from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.lead_follow_up_repository import (
    LeadFollowUpRepository,
)
from app.database.appointment_repository import AppointmentRepository
from app.database.session import get_db
from app.schemas.lead_follow_up import (
    LeadFollowUpAttemptCreateRequest,
    LeadFollowUpAttemptResponse,
    LeadFollowUpCreateRequest,
    LeadFollowUpResponse,
)
from app.services.lead_follow_up_service import (
    LeadFollowUpService,
)


router = APIRouter(
    prefix="/follow-ups",
    tags=["Follow-ups"],
)


def _lead_follow_up_service(
        db: Session,
) -> LeadFollowUpService:
    return LeadFollowUpService(
        follow_up_repository=LeadFollowUpRepository(db),
        appointment_repository=AppointmentRepository(db),
    )


@router.post(
    "",
    response_model=LeadFollowUpResponse,
)
def create_follow_up(
        request: LeadFollowUpCreateRequest,
        db: Session = Depends(get_db),
) -> LeadFollowUpResponse:
    follow_up = _lead_follow_up_service(db).schedule(
        lead_id=request.lead_id,
        appointment_id=request.appointment_id,
        scheduled_at=request.scheduled_at,
    )

    return LeadFollowUpResponse.model_validate(
        follow_up
    )


@router.get(
    "/{follow_up_id}",
    response_model=LeadFollowUpResponse,
)
def get_follow_up(
        follow_up_id: int,
        db: Session = Depends(get_db),
) -> LeadFollowUpResponse:
    follow_up = _lead_follow_up_service(
        db
    ).get_by_id(
        follow_up_id
    )

    return LeadFollowUpResponse.model_validate(
        follow_up
    )


@router.post(
    "/{follow_up_id}/cancel",
    response_model=LeadFollowUpResponse,
)
def cancel_follow_up(
        follow_up_id: int,
        db: Session = Depends(get_db),
) -> LeadFollowUpResponse:
    follow_up = _lead_follow_up_service(
        db
    ).cancel(
        follow_up_id
    )

    return LeadFollowUpResponse.model_validate(
        follow_up
    )


@router.post(
    "/{follow_up_id}/attempts",
    response_model=LeadFollowUpAttemptResponse,
)
def register_follow_up_attempt(
        follow_up_id: int,
        request: LeadFollowUpAttemptCreateRequest,
        db: Session = Depends(get_db),
) -> LeadFollowUpAttemptResponse:
    attempt = _lead_follow_up_service(
        db
    ).register_attempt(
        follow_up_id=follow_up_id,
        channel=request.channel,
        status=request.status,
        message=request.message,
    )

    return LeadFollowUpAttemptResponse.model_validate(
        attempt
    )
