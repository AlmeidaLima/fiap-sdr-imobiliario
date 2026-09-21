from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    ask_question_node,
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


def build_sdr_graph(
        property_search_service: ConversationPropertySearchService,
):
    graph = StateGraph(AgentState)

    graph.add_node(
        "process_message",
        process_message_node,
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
            property_search_service,
        ),
    )

    graph.add_edge(
        START,
        "process_message",
    )

    graph.add_edge(
        "process_message",
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
        END,
    )

    graph.add_edge(
        ROUTE_SEARCH_PROPERTIES,
        END,
    )

    return graph.compile()