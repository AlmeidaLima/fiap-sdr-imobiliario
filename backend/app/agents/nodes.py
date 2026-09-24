from app.agents.state import AgentState
from app.schemas.conversation import ConversationState
from app.services.conversation_service import ConversationService
from app.services.conversation_qualification_service import (
    ConversationQualificationService,
)
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)
from app.services.llm_client import LLMClientError
from app.services.llm_service import LLMService
from app.services.lead_score_service import LeadScoreService

def process_message_node(state: AgentState) -> dict:
    conversation_id = state["conversation_id"]
    message = state["message"]

    conversation_state = state.get("conversation_state")

    if conversation_state is None:
        conversation_state = ConversationState(
            conversation_id=conversation_id,
        )

    conversation_service = ConversationService()

    updated_state = conversation_service.process_message(
        state=conversation_state,
        message=message,
    )

    return {
        "conversation_state": updated_state,
    }


def calculate_lead_score_node(state: AgentState) -> dict:
    conversation_state = state["conversation_state"]
    result = LeadScoreService().calculate(conversation_state)

    updated_state = conversation_state.model_copy(
        update={
            "lead_score": result.score,
            "lead_classification": result.classification,
        }
    )

    return {
        "conversation_state": updated_state,
    }

def qualify_conversation_node(state: AgentState) -> dict:
    conversation_state = state["conversation_state"]

    qualification_service = ConversationQualificationService()

    qualification = qualification_service.qualify(
        conversation_state,
    )

    return {
        "qualification": qualification,
    }

def ask_question_node(state: AgentState) -> dict:
    qualification = state["qualification"]

    return {
        "response": qualification.next_question,
    }

def search_properties_node(
        state: AgentState,
        property_search_service: ConversationPropertySearchService,
) -> dict:
    conversation_state = state["conversation_state"]

    properties = property_search_service.search(
        conversation_state,
        limit=state.get("limit", 5),
    )

    return {
        "properties": properties,
    }


def generate_response_node(
        state: AgentState,
        llm_service: LLMService,
) -> dict:
    properties = state.get("properties", [])
    properties_context = [
        _property_to_context(property_embedding.property)
        for property_embedding, _ in properties
    ]

    try:
        response = llm_service.generate_response(
            user_message=state["message"],
            conversation_state=state["conversation_state"],
            qualification=state["qualification"],
            conversation_history=state.get("conversation_history", []),
            properties_context=properties_context,
        )
    except LLMClientError:
        response = _build_fallback_response(state)

    return {
        "response": response,
    }


def _property_to_context(property_model) -> dict:
    description = property_model.description

    if description:
        description = description[:1000]

    context = {
        "id": property_model.id,
        "external_id": property_model.external_id,
        "title": property_model.title,
        "description": description,
        "neighborhood": property_model.neighborhood,
        "usable_area": property_model.usable_area,
        "bedrooms": property_model.bedrooms,
        "bathrooms": property_model.bathrooms,
        "parking_spaces": property_model.parking_spaces,
        "price": str(property_model.price),
    }

    return {
        key: value
        for key, value in context.items()
        if value is not None
    }


def _build_fallback_response(state: AgentState) -> str:
    qualification = state["qualification"]

    if not qualification.qualified and qualification.next_question:
        return qualification.next_question

    properties = state.get("properties", [])

    if properties:
        return (
            f"Encontrei {len(properties)} imóvel(is) compatível(is) com os "
            "critérios informados. Confira as opções encontradas."
        )

    return (
        "Não encontrei imóveis compatíveis com esses critérios. "
        "Podemos ajustar o bairro, o orçamento ou a quantidade de quartos."
    )
