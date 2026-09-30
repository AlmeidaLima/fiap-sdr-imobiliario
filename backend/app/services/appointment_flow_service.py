
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, time

from app.schemas.conversation import ConversationState
from app.services.lead_identification_service import LeadIdentificationService


@dataclass(frozen=True)
class AppointmentFlowResult:
    state: ConversationState
    response: str


class AppointmentFlowService:
    ACTIVE_STAGES = {
        "SELECTED",
        "AWAITING_TYPE",
        "AWAITING_DATE",
        "AWAITING_TIME",
        "AWAITING_NAME",
        "AWAITING_CONFIRMATION",
        "CONFIRMED",
        "CANCELLED",
    }

    CONFIRMATION_PATTERN = re.compile(
        r"^(?:sim|confirmo|pode confirmar)"
        r"(?:,?\s+confirmo(?:\s+(?:a visita|a reuniao))?"
        r"|\s+(?:a visita|a reuniao))?[.!]?$"
    )

    CANCELLATION_PATTERN = re.compile(
        r"^(?:nao|cancelar|nao quero mais)[.!]?$"
    )

    DATE_PATTERN = re.compile(
        r"\b(\d{2})/(\d{2})/(\d{4})\b"
    )

    TIME_PATTERN = re.compile(
        r"\b([01]?\d|2[0-3])(?::([0-5]\d)|h(?:([0-5]\d))?)\b"
    )

    DIRECT_NAME_PATTERN = re.compile(
        r"[A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,3}"
    )

    INVALID_DIRECT_NAMES = {
        "sim",
        "não",
        "nao",
        "confirmo",
        "cancelar",
        "visita",
        "reunião",
        "reuniao",
        "quero",
        "agendar",
        "quero visitar",
        "quero agendar",
        "pode confirmar",
    }

    def __init__(
            self,
            today_provider: Callable[[], date] = date.today,
    ):
        self.today_provider = today_provider
        self.lead_identification_service = LeadIdentificationService()

    def process(
            self,
            state: ConversationState,
            message: str,
    ) -> AppointmentFlowResult:
        normalized_message = self._normalize_text(message)

        if state.appointment_stage == "CONFIRMED":
            return AppointmentFlowResult(
                state=state,
                response=self._confirmed_response(state),
            )

        if state.appointment_stage == "CANCELLED":
            return AppointmentFlowResult(
                state=state,
                response="A coleta do agendamento está cancelada.",
            )

        if self.CANCELLATION_PATTERN.fullmatch(normalized_message):
            return AppointmentFlowResult(
                state=state.model_copy(
                    update={"appointment_stage": "CANCELLED"},
                ),
                response="A coleta do agendamento foi cancelada.",
            )

        if state.appointment_stage == "SELECTED":
            return AppointmentFlowResult(
                state=state.model_copy(
                    update={"appointment_stage": "AWAITING_TYPE"},
                ),
                response=(
                    "Você prefere agendar uma visita ao imóvel selecionado "
                    "ou uma reunião?"
                ),
            )

        if state.appointment_stage == "AWAITING_TYPE":
            return self._process_type(state, normalized_message)

        if state.appointment_stage == "AWAITING_DATE":
            return self._process_date(state, message)

        if state.appointment_stage == "AWAITING_TIME":
            return self._process_time(state, normalized_message)

        if state.appointment_stage == "AWAITING_NAME":
            return self._process_name(state, message)

        if state.appointment_stage == "AWAITING_CONFIRMATION":
            return self._process_confirmation(state, normalized_message)

        return AppointmentFlowResult(
            state=state,
            response="Não existe uma coleta de agendamento ativa.",
        )

    @classmethod
    def is_active(cls, state: ConversationState) -> bool:
        return state.appointment_stage in cls.ACTIVE_STAGES

    def _process_type(
            self,
            state: ConversationState,
            message: str,
    ) -> AppointmentFlowResult:
        appointment_type = self._extract_type(message)

        if appointment_type is None:
            return AppointmentFlowResult(
                state=state,
                response="Informe se você prefere VISITA ou REUNIÃO.",
            )

        return AppointmentFlowResult(
            state=state.model_copy(
                update={
                    "appointment_stage": "AWAITING_DATE",
                    "appointment_type": appointment_type,
                },
            ),
            response="Informe a data desejada no formato DD/MM/AAAA.",
        )

    def _process_date(
            self,
            state: ConversationState,
            message: str,
    ) -> AppointmentFlowResult:
        appointment_date = self._extract_date(message)

        if (
                appointment_date is None
                or appointment_date < self.today_provider()
        ):
            return AppointmentFlowResult(
                state=state,
                response=(
                    "Informe uma data válida, atual ou futura, "
                    "no formato DD/MM/AAAA."
                ),
            )

        return AppointmentFlowResult(
            state=state.model_copy(
                update={
                    "appointment_stage": "AWAITING_TIME",
                    "appointment_date": appointment_date,
                },
            ),
            response=(
                "Informe o horário desejado, "
                "por exemplo 14:00, 14h ou 14h30."
            ),
        )

    def _process_time(
            self,
            state: ConversationState,
            message: str,
    ) -> AppointmentFlowResult:
        appointment_time = self._extract_time(message)

        if appointment_time is None:
            return AppointmentFlowResult(
                state=state,
                response=(
                    "Informe um horário válido, "
                    "por exemplo 14:00, 14h ou 14h30."
                ),
            )

        next_stage = (
            "AWAITING_CONFIRMATION"
            if state.lead_name
            else "AWAITING_NAME"
        )

        updated_state = state.model_copy(
            update={
                "appointment_stage": next_stage,
                "appointment_time": appointment_time,
            },
        )

        if next_stage == "AWAITING_NAME":
            return AppointmentFlowResult(
                state=updated_state,
                response=(
                    "Para finalizar o agendamento, "
                    "qual é o seu nome?"
                ),
            )

        return AppointmentFlowResult(
            state=updated_state,
            response=self._confirmation_summary(updated_state),
        )

    def _process_name(
            self,
            state: ConversationState,
            message: str,
    ) -> AppointmentFlowResult:
        name = self.lead_identification_service.extract_name(message)

        if name is None:
            candidate = message.strip()

            if (
                    self.DIRECT_NAME_PATTERN.fullmatch(candidate)
                    and self._normalize_text(candidate)
                    not in self.INVALID_DIRECT_NAMES
            ):
                name = " ".join(
                    word.capitalize()
                    for word in candidate.split()
                )

        if name is None:
            return AppointmentFlowResult(
                state=state,
                response=(
                    "Informe seu nome para continuar o agendamento. "
                    "Por exemplo: Meu nome é Rafael Almeida."
                ),
            )

        updated_state = state.model_copy(
            update={
                "lead_name": name,
                "appointment_stage": "AWAITING_CONFIRMATION",
            },
        )

        return AppointmentFlowResult(
            state=updated_state,
            response=self._confirmation_summary(updated_state),
        )

    def _process_confirmation(
            self,
            state: ConversationState,
            message: str,
    ) -> AppointmentFlowResult:
        if not self.CONFIRMATION_PATTERN.fullmatch(message):
            return AppointmentFlowResult(
                state=state,
                response=self._confirmation_summary(state),
            )

        updated_state = state.model_copy(
            update={"appointment_stage": "CONFIRMED"},
        )

        return AppointmentFlowResult(
            state=updated_state,
            response=self._confirmed_response(updated_state),
        )

    @staticmethod
    def _extract_type(message: str) -> str | None:
        if re.search(r"\b(?:visita|visitar)\b", message):
            return "VISITA"

        if re.search(r"\breuniao\b", message):
            return "REUNIAO"

        return None

    @classmethod
    def _extract_date(cls, message: str) -> date | None:
        match = cls.DATE_PATTERN.search(message)

        if match is None:
            return None

        day, month, year = map(int, match.groups())

        try:
            return date(year, month, day)
        except ValueError:
            return None

    @classmethod
    def _extract_time(cls, message: str) -> time | None:
        match = cls.TIME_PATTERN.search(message)

        if match is None:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2) or match.group(3) or 0)

        return time(hour, minute)

    @staticmethod
    def _confirmation_summary(state: ConversationState) -> str:
        appointment_type = (
            "Visita"
            if state.appointment_type == "VISITA"
            else "Reunião"
        )

        appointment_date = state.appointment_date.strftime("%d/%m/%Y")
        appointment_time = state.appointment_time.strftime("%H:%M")

        return (
            f"{appointment_type} referente ao imóvel "
            f"{state.selected_property_id}, "
            f"em {appointment_date} às {appointment_time}. "
            "Confirmar?"
        )

    @staticmethod
    def _confirmed_response(state: ConversationState) -> str:
        appointment_date = state.appointment_date.strftime("%d/%m/%Y")
        appointment_time = state.appointment_time.strftime("%H:%M")

        return (
            "Dados do agendamento confirmados para "
            f"{appointment_date} às {appointment_time}. "
            "Finalizando o agendamento..."
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)

        without_accents = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        return re.sub(
            r"\s+",
            " ",
            without_accents.strip().lower(),
        )
