import hashlib
from collections.abc import Callable
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ApplicationException
from app.database.appointment_repository import AppointmentRepository
from app.database.conversation_repository import ConversationRepository
from app.database.property_repository import PropertyRepository
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.schemas.conversation import ConversationState
from app.services.lead_score_service import LeadScoreService


class AppointmentService:
    def __init__(
            self,
            appointment_repository: AppointmentRepository,
            conversation_repository: ConversationRepository,
            property_repository: PropertyRepository,
            business_timezone: str,
            lead_score_service: LeadScoreService | None = None,
            now_provider: Callable[[], datetime] = (
                lambda: datetime.now(timezone.utc)
            ),
    ):
        self.appointment_repository = appointment_repository
        self.conversation_repository = conversation_repository
        self.property_repository = property_repository
        self.business_timezone = ZoneInfo(business_timezone)
        self.lead_score_service = lead_score_service or LeadScoreService()
        self.now_provider = now_provider

    def create_from_conversation(
            self,
            conversation_id: str,
    ) -> Appointment:
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
        self._validate(conversation, state)

        scheduled_at = datetime.combine(
            state.appointment_date,
            state.appointment_time,
            tzinfo=self.business_timezone,
        ).astimezone(timezone.utc)

        if scheduled_at <= self._current_utc_time():
            raise ApplicationException(
                detail="A data e o horário do agendamento devem ser futuros.",
                error="appointment_in_past",
            )

        idempotency_key = self.build_idempotency_key(
            conversation=conversation,
            state=state,
            scheduled_at=scheduled_at,
        )
        appointment = (
            self.appointment_repository.get_by_idempotency_key(
                idempotency_key
            )
        )

        if appointment is None:
            appointment = Appointment(
                lead_id=conversation.lead_id,
                property_id=state.selected_property_id,
                appointment_type=state.appointment_type,
                scheduled_at=scheduled_at,
                status="CONFIRMED",
                idempotency_key=idempotency_key,
            )
            try:
                appointment = self.appointment_repository.create(appointment)
            except IntegrityError:
                self.appointment_repository.rollback()
                appointment = (
                    self.appointment_repository.get_by_idempotency_key(
                        idempotency_key
                    )
                )
                if appointment is None:
                    raise

        self._persist_commercial_state(conversation, state, appointment.id)
        return appointment

    def create_from_conversation_with_state(
            self,
            conversation_id: str,
    ) -> tuple[Appointment, ConversationState]:
        appointment = self.create_from_conversation(conversation_id)
        conversation = self.conversation_repository.find_by_conversation_id(
            conversation_id
        )
        state = ConversationState(
            conversation_id=conversation.conversation_id,
            **(conversation.state or {}),
        )
        return appointment, state

    def get_by_id(self, appointment_id: int) -> Appointment:
        appointment = self.appointment_repository.get_by_id(appointment_id)
        if appointment is None:
            raise ApplicationException(
                detail="Agendamento não encontrado.",
                status_code=404,
                error="appointment_not_found",
            )
        return appointment

    @staticmethod
    def build_idempotency_key(
            conversation: Conversation,
            state: ConversationState,
            scheduled_at: datetime,
    ) -> str:
        canonical_value = "|".join(
            [
                conversation.conversation_id,
                str(conversation.lead_id),
                str(state.selected_property_id or ""),
                str(state.appointment_type),
                scheduled_at.isoformat(),
            ]
        )
        return hashlib.sha256(canonical_value.encode("utf-8")).hexdigest()

    def _validate(
            self,
            conversation: Conversation,
            state: ConversationState,
    ) -> None:
        if conversation.lead_id is None:
            raise ApplicationException(
                detail="A conversa não possui lead associado.",
                error="conversation_without_lead",
            )
        if state.appointment_stage != "CONFIRMED":
            raise ApplicationException(
                detail="Os dados do agendamento ainda não foram confirmados.",
                error="appointment_not_confirmed",
            )
        if state.appointment_type is None:
            raise ApplicationException(
                detail="O tipo do agendamento não foi informado.",
                error="missing_appointment_type",
            )
        if state.appointment_date is None or state.appointment_time is None:
            raise ApplicationException(
                detail="A data e o horário do agendamento são obrigatórios.",
                error="missing_appointment_schedule",
            )
        if (
                state.appointment_type == "VISITA"
                and state.selected_property_id is None
        ):
            raise ApplicationException(
                detail="Uma visita exige um imóvel selecionado.",
                error="missing_selected_property",
            )
        if (
                state.selected_property_id is not None
                and self.property_repository.find_by_id(
                    state.selected_property_id
                ) is None
        ):
            raise ApplicationException(
                detail="O imóvel selecionado não existe.",
                error="property_not_found",
            )

    def _current_utc_time(self) -> datetime:
        current = self.now_provider()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc)

    def _persist_commercial_state(
            self,
            conversation: Conversation,
            state: ConversationState,
            appointment_id: int,
    ) -> None:
        updated_state = state.model_copy(
            update={
                "appointment_id": appointment_id,
                "accepted_meeting_or_visit": True,
            },
        )
        score_result = self.lead_score_service.calculate(updated_state)
        updated_state = updated_state.model_copy(
            update={
                "lead_score": score_result.score,
                "lead_classification": score_result.classification,
            },
        )

        if updated_state == state:
            return

        self.conversation_repository.update_state(
            conversation=conversation,
            state=updated_state.model_dump(
                exclude={"conversation_id"},
                mode="json",
            ),
        )
