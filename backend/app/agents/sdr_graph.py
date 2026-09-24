from langgraph.graph import END, START, StateGraph
from collections.abc import Callable
from app.agents.nodes import (
    ask_question_node,
    calculate_lead_score_node,
    generate_response_node,
    process_message_node,
    qualify_conversation_node,
    search_properties_node,
)
from app.agents.routing import (
    ROUTE_ASK_QUESTION,
    ROUTE_SEARCH_PROPERTIES,
    route_after_qualification,
)
from app.agents.state import AgentState
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)
from app.services.llm_service import LLMService


def build_sdr_graph(
        property_search_service_factory: Callable[
            [],
            ConversationPropertySearchService,
        ],
        llm_service_factory: Callable[[], LLMService],
):
    graph = StateGraph(AgentState)

    graph.add_node(
        "process_message",
        process_message_node,
    )

    graph.add_node(
        "calculate_lead_score",
        calculate_lead_score_node,
    )

    graph.add_node(
        "qualify_conversation",
        qualify_conversation_node,
    )

    graph.add_node(
        ROUTE_ASK_QUESTION,
        ask_question_node,
    )

    graph.add_node(
        ROUTE_SEARCH_PROPERTIES,
        lambda state: search_properties_node(
            state,
            property_search_service_factory(),
        ),
    )

    graph.add_node(
        "generate_response",
        lambda state: generate_response_node(
            state,
            llm_service_factory(),
        ),
    )

    graph.add_edge(
        START,
        "process_message",
    )

    graph.add_edge(
        "process_message",
        "calculate_lead_score",
    )

    graph.add_edge(
        "calculate_lead_score",
        "qualify_conversation",
    )

    graph.add_conditional_edges(
        "qualify_conversation",
        route_after_qualification,
        {
            ROUTE_ASK_QUESTION: ROUTE_ASK_QUESTION,
            ROUTE_SEARCH_PROPERTIES: ROUTE_SEARCH_PROPERTIES,
        },
    )

    graph.add_edge(
        ROUTE_ASK_QUESTION,
        "generate_response",
    )

    graph.add_edge(
        ROUTE_SEARCH_PROPERTIES,
        "generate_response",
    )

    graph.add_edge(
        "generate_response",
        END,
    )

    return graph.compile()
