from app.agents.state import AgentState
from app.schemas.conversation import ConversationState
from app.services.conversation_service import ConversationService
from app.services.conversation_qualification_service import (
    ConversationQualificationService,
)
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)

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