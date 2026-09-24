from collections.abc import Callable
from app.agents.sdr_graph import build_sdr_graph
from app.agents.state import AgentState
from app.schemas.conversation import ConversationState, ConversationTurnResult
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)


class SDRAgentService:

    def __init__(
            self,
            property_search_service_factory: Callable[
                [],
                ConversationPropertySearchService,
            ],
    ):
        self.graph = build_sdr_graph(
            property_search_service_factory=property_search_service_factory,
        )

    def process_turn(
            self,
            conversation_state: ConversationState,
            message: str,
            limit: int = 5,
        ) -> ConversationTurnResult:

        initial_state: AgentState = {
            "conversation_id": conversation_state.conversation_id,
            "message": message,
            "limit": limit,
            "conversation_state": conversation_state,
        }

        result = self.graph.invoke(initial_state)

        return ConversationTurnResult(
            state=result["conversation_state"],
            qualification=result["qualification"],
            properties=result.get("properties", []),
        )