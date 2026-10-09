from app.core.exceptions import ApplicationException
from app.database.appointment_repository import AppointmentRepository
from app.database.dashboard_repository import (
    DashboardLeadRecord,
    DashboardRepository,
)
from app.database.property_repository import PropertyRepository
from app.models.appointment import Appointment
from app.models.message import Message
from app.models.property import Property
from app.schemas.conversation import ConversationState
from app.schemas.dashboard import (
    DashboardAppointment,
    DashboardLeadDetailResponse,
    DashboardLeadListResponse,
    DashboardLeadSummary,
    DashboardMessage,
    DashboardPreferences,
    DashboardProperty,
)
from app.services.lead_handoff_service import LeadHandoffService


class DashboardService:
    def __init__(
            self,
            dashboard_repository: DashboardRepository,
            property_repository: PropertyRepository,
            appointment_repository: AppointmentRepository,
            lead_handoff_service: LeadHandoffService,
    ):
        self.dashboard_repository = dashboard_repository
        self.property_repository = property_repository
        self.appointment_repository = appointment_repository
        self.lead_handoff_service = lead_handoff_service

    def list_leads(self) -> DashboardLeadListResponse:
        records = self.dashboard_repository.list_leads()
        return DashboardLeadListResponse(
            leads=[self._build_lead(record) for record in records],
        )

    def get_lead_detail(self, lead_id: int) -> DashboardLeadDetailResponse:
        lead = self.dashboard_repository.get_lead(lead_id)
        if lead is None:
            self._raise_lead_not_found()

        record = self.dashboard_repository.get_lead_record(lead_id)
        if record is None:
            self._raise_lead_not_found()

        state = self._build_state(record)
        recommended_properties = self.property_repository.find_by_ids(
            state.presented_property_ids,
        )
        selected_property = None
        if state.selected_property_id is not None:
            selected_property = self.property_repository.find_by_id(
                state.selected_property_id,
            )

        history = self.dashboard_repository.list_public_messages(
            record.conversation.id,
        )
        appointments = self.appointment_repository.list_by_lead_id(lead_id)
        summary = self.lead_handoff_service.get_by_conversation_id(
            record.conversation.conversation_id,
        )

        return DashboardLeadDetailResponse(
            lead=self._build_lead(record, state),
            preferences=self._build_preferences(state),
            history=[self._build_message(message) for message in history],
            recommended_properties=[
                self._build_property(property_)
                for property_ in recommended_properties
            ],
            selected_property=(
                self._build_property(selected_property)
                if selected_property is not None
                else None
            ),
            summary=summary,
            appointments=[
                self._build_appointment(appointment)
                for appointment in appointments
            ],
        )

    @staticmethod
    def _build_state(record: DashboardLeadRecord) -> ConversationState:
        return ConversationState(
            conversation_id=record.conversation.conversation_id,
            **(record.conversation.state or {}),
        )

    def _build_lead(
            self,
            record: DashboardLeadRecord,
            state: ConversationState | None = None,
    ) -> DashboardLeadSummary:
        state = state or self._build_state(record)
        return DashboardLeadSummary(
            lead_id=record.lead.id,
            conversation_id=record.conversation.conversation_id,
            name=record.lead.name,
            status=record.lead.status,
            commercial_intent=state.commercial_intent,
            score=state.lead_score,
            classification=state.lead_classification,
            last_interaction_at=record.last_interaction_at,
        )

    @staticmethod
    def _build_preferences(state: ConversationState) -> DashboardPreferences:
        return DashboardPreferences(
            urgency_days=state.urgency_days,
            neighborhood=state.neighborhood,
            min_price=state.min_price,
            max_price=state.max_price,
            min_bedrooms=state.min_bedrooms,
            min_bathrooms=state.min_bathrooms,
            min_parking_spaces=state.min_parking_spaces,
            min_usable_area=state.min_usable_area,
            semantic_preferences=state.semantic_preferences,
        )

    @staticmethod
    def _build_message(message: Message) -> DashboardMessage:
        return DashboardMessage(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )

    @staticmethod
    def _build_property(property_: Property) -> DashboardProperty:
        return DashboardProperty(
            id=property_.id,
            external_id=property_.external_id,
            title=property_.title,
            description=property_.description,
            neighborhood=property_.neighborhood,
            price=property_.price,
            bedrooms=property_.bedrooms,
            bathrooms=property_.bathrooms,
            parking_spaces=property_.parking_spaces,
            usable_area=property_.usable_area,
        )

    @staticmethod
    def _build_appointment(appointment: Appointment) -> DashboardAppointment:
        return DashboardAppointment(
            id=appointment.id,
            property_id=appointment.property_id,
            appointment_type=appointment.appointment_type,
            scheduled_at=appointment.scheduled_at,
            status=appointment.status,
            notes=appointment.notes,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
        )

    @staticmethod
    def _raise_lead_not_found() -> None:
        raise ApplicationException(
            detail="Lead não encontrado ou sem contexto conversacional.",
            status_code=404,
            error="lead_not_found",
        )
