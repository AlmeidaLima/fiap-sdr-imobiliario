from app.agents.state import AgentState


ROUTE_ASK_QUESTION = "ask_question"
ROUTE_SEARCH_PROPERTIES = "search_properties"


def route_after_qualification(state: AgentState) -> str:
    qualification = state["qualification"]

    if qualification.qualified:
        return ROUTE_SEARCH_PROPERTIES

    return ROUTE_ASK_QUESTION