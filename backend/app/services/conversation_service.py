from app.schemas.conversation import (
    ConversationState,
    ConversationTurnResult,
)
from app.schemas.property_search_intent import (
    PropertySearchIntent,
)
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)
from app.services.commercial_qualification_service import (
    CommercialQualificationService,
)
from app.services.conversation_qualification_service import (
    ConversationQualificationService,
)
from app.services.lead_identification_service import (
    LeadIdentificationService,
)
from app.services.property_search_intent_service import (
    PropertySearchIntentService,
)
from app.services.property_selection_service import PropertySelectionService


class ConversationService:
    """
    Responsável por manter e atualizar o estado acumulado
    da conversa com o cliente.

    Responsabilidades:
    - interpretar novas mensagens;
    - identificar o nome do lead;
    - combinar novas informações com o estado anterior;
    - preservar informações já conhecidas;
    - atualizar informações alteradas pelo cliente;
    - acumular preferências semânticas;
    - avaliar a qualificação da conversa;
    - buscar imóveis quando a conversa estiver qualificada.
    """

    def __init__(
            self,
            intent_service: PropertySearchIntentService | None = None,
            qualification_service: ConversationQualificationService | None = None,
            property_search_service: ConversationPropertySearchService | None = None,
            lead_identification_service: LeadIdentificationService | None = None,
            commercial_qualification_service: CommercialQualificationService | None = None,
    ):
        self.intent_service = (
                intent_service
                or PropertySearchIntentService()
        )

        self.qualification_service = (
                qualification_service
                or ConversationQualificationService()
        )

        self.property_search_service = (
            property_search_service
        )

        self.lead_identification_service = (
                lead_identification_service
                or LeadIdentificationService()
        )

        self.commercial_qualification_service = (
                commercial_qualification_service
                or CommercialQualificationService()
        )

    def merge_intent(
            self,
            state: ConversationState,
            intent: PropertySearchIntent,
    ) -> ConversationState:
        """
        Combina a intenção da mensagem atual com o estado anterior.

        Regras:
        - valores não informados na nova mensagem preservam
          o estado anterior;
        - valores informados substituem os anteriores;
        - preferências semânticas são acumuladas;
        - preferências semânticas duplicadas não são adicionadas.
        """

        state_data = state.model_dump()

        intent_data = intent.model_dump(
            exclude_none=True,
        )

        semantic_query = intent_data.pop(
            "semantic_query",
            None,
        )

        for field, value in intent_data.items():
            if field in state_data:
                state_data[field] = value

        if semantic_query:
            preferences = list(
                state_data.get(
                    "semantic_preferences",
                    [],
                )
            )

            if semantic_query not in preferences:
                preferences.append(
                    semantic_query
                )

            state_data["semantic_preferences"] = (
                preferences
            )

        return ConversationState(
            **state_data
        )

    def process_message(
            self,
            state: ConversationState,
            message: str,
    ) -> ConversationState:
        """
        Processa uma nova mensagem do cliente.

        Fluxo:
        mensagem
            -> PropertySearchIntentService
            -> PropertySearchIntent
            -> merge com estado anterior
            -> LeadIdentificationService
            -> identificação do nome do lead
            -> ConversationState atualizado
        """

        intent = self.intent_service.parse(
            message
        )

        updated_state = self.merge_intent(
            state,
            intent,
        )

        lead_name = (
            self.lead_identification_service.extract_name(
                message
            )
        )

        if lead_name is not None:
            updated_state.lead_name = lead_name

        commercial_qualification = (
            self.commercial_qualification_service.extract(
                message
            )
        )

        if commercial_qualification.commercial_intent != "INDEFINIDO":
            updated_state.commercial_intent = (
                commercial_qualification.commercial_intent
            )

        if commercial_qualification.urgency_days is not None:
            updated_state.urgency_days = (
                commercial_qualification.urgency_days
            )

        if updated_state.appointment_id is None:
            updated_state.accepted_meeting_or_visit = False

        return updated_state

    def process_turn(
            self,
            state: ConversationState,
            message: str,
    ) -> ConversationTurnResult:
        """
        Processa um turno completo da conversa.

        Fluxo:
        mensagem
            -> interpretação da intenção
            -> identificação do lead
            -> atualização da memória
            -> qualificação
            -> próxima pergunta, quando ainda faltarem dados
            -> busca de imóveis, quando qualificado
        """

        updated_state = self.process_message(
            state,
            message,
        )

        qualification = (
            self.qualification_service.qualify(
                updated_state
            )
        )

        properties = []

        if (
                qualification.qualified
                and self.property_search_service is not None
        ):
            properties = (
                self.property_search_service.search(
                    updated_state
                )
            )
            updated_state = (
                PropertySelectionService().register_presented_properties(
                    updated_state,
                    [
                        property_embedding.property.id
                        for property_embedding, _ in properties
                    ],
                )
            )

        return ConversationTurnResult(
            state=updated_state,
            qualification=qualification,
            properties=properties,
            response=(
                qualification.next_question
                or "Consulta de imóveis concluída."
            ),
        )
