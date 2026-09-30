from app.core.exceptions import ApplicationException
from app.database.appointment_repository import AppointmentRepository
from app.database.conversation_repository import ConversationRepository
from app.database.lead_repository import LeadRepository
from app.database.property_repository import PropertyRepository
from app.models.appointment import Appointment
from app.models.lead import Lead
from app.models.property import Property
from app.schemas.conversation import ConversationState
from app.schemas.lead_handoff import (
    LeadHandoffAppointment,
    LeadHandoffLead,
    LeadHandoffProperty,
    LeadHandoffQualification,
    LeadHandoffResponse,
)


class LeadHandoffService:
    def __init__(
            self,
            conversation_repository: ConversationRepository,
            lead_repository: LeadRepository,
            property_repository: PropertyRepository,
            appointment_repository: AppointmentRepository,
    ):
        self.conversation_repository = conversation_repository
        self.lead_repository = lead_repository
        self.property_repository = property_repository
        self.appointment_repository = appointment_repository

    def get_by_conversation_id(
            self,
            conversation_id: str,
    ) -> LeadHandoffResponse:
        conversation = self.conversation_repository.find_by_conversation_id(
            conversation_id
        )
        if conversation is None:
            raise ApplicationException(
                detail="Conversa não encontrada.",
                status_code=404,
                error="conversation_not_found",
            )

        state = ConversationState(
            conversation_id=conversation.conversation_id,
            **(conversation.state or {}),
        )
        qualification = self._build_qualification(state)

        lead = None
        if conversation.lead_id is not None:
            lead = self.lead_repository.find_by_id(conversation.lead_id)

        lead_projection = self._build_lead(lead, state)
        ready_data = self._get_ready_data(
            conversation_lead_id=conversation.lead_id,
            state=state,
            lead=lead,
        )

        if ready_data is None:
            return LeadHandoffResponse(
                conversation_id=conversation.conversation_id,
                handoff_status="NOT_READY",
                lead=lead_projection,
                qualification=qualification,
                property=None,
                appointment=None,
            )

        appointment, property_ = ready_data
        return LeadHandoffResponse(
            conversation_id=conversation.conversation_id,
            handoff_status="READY",
            lead=lead_projection,
            qualification=qualification,
            property=self._build_property(property_),
            appointment=self._build_appointment(appointment),
        )

    def _get_ready_data(
            self,
            conversation_lead_id: int | None,
            state: ConversationState,
            lead: Lead | None,
    ) -> tuple[Appointment, Property | None] | None:
        if (
                conversation_lead_id is None
                or lead is None
                or state.appointment_id is None
                or not state.accepted_meeting_or_visit
        ):
            return None

        appointment = self.appointment_repository.get_by_id(
            state.appointment_id
        )
        if (
                appointment is None
                or appointment.lead_id != conversation_lead_id
                or appointment.status != "CONFIRMED"
                or appointment.appointment_type not in {"VISITA", "REUNIAO"}
        ):
            return None

        if appointment.appointment_type == "VISITA":
            if (
                    appointment.property_id is None
                    or state.selected_property_id is None
                    or appointment.property_id != state.selected_property_id
            ):
                return None

            property_ = self.property_repository.find_by_id(
                appointment.property_id
            )
            if property_ is None:
                return None

            return appointment, property_

        if appointment.property_id is None:
            return appointment, None

        if (
                state.selected_property_id is None
                or appointment.property_id != state.selected_property_id
        ):
            return None

        property_ = self.property_repository.find_by_id(
            appointment.property_id
        )
        if property_ is None:
            return None

        return appointment, property_

    @staticmethod
    def _build_lead(
            lead: Lead | None,
            state: ConversationState,
    ) -> LeadHandoffLead | None:
        if lead is None:
            return None

        return LeadHandoffLead(
            id=lead.id,
            name=lead.name,
            score=state.lead_score,
            classification=state.lead_classification,
        )

    @staticmethod
    def _build_qualification(
            state: ConversationState,
    ) -> LeadHandoffQualification:
        return LeadHandoffQualification(
            commercial_intent=state.commercial_intent,
            urgency_days=state.urgency_days,
            neighborhood=state.neighborhood,
            min_price=state.min_price,
            max_price=state.max_price,
            min_bedrooms=state.min_bedrooms,
            min_bathrooms=state.min_bathrooms,
            min_parking_spaces=state.min_parking_spaces,
            min_usable_area=state.min_usable_area,
        )

    @staticmethod
    def _build_property(
            property_: Property | None,
    ) -> LeadHandoffProperty | None:
        if property_ is None:
            return None

        return LeadHandoffProperty(
            id=property_.id,
            external_id=property_.external_id,
            title=property_.title,
            neighborhood=property_.neighborhood,
            price=property_.price,
            bedrooms=property_.bedrooms,
            bathrooms=property_.bathrooms,
            parking_spaces=property_.parking_spaces,
            usable_area=property_.usable_area,
        )

    @staticmethod
    def _build_appointment(
            appointment: Appointment,
    ) -> LeadHandoffAppointment:
        return LeadHandoffAppointment(
            id=appointment.id,
            appointment_type=appointment.appointment_type,
            scheduled_at=appointment.scheduled_at,
            status=appointment.status,
        )
