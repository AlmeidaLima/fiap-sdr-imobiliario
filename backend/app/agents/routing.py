from app.agents.state import AgentState
from app.services.appointment_flow_service import AppointmentFlowService


ROUTE_ASK_QUESTION = "ask_question"
ROUTE_SEARCH_PROPERTIES = "search_properties"
ROUTE_APPOINTMENT_FLOW = "appointment_flow"


def route_after_qualification(state: AgentState) -> str:
    conversation_state = state["conversation_state"]

    if AppointmentFlowService.is_active(conversation_state):
        return ROUTE_APPOINTMENT_FLOW

    qualification = state["qualification"]

    if qualification.qualified:
        return ROUTE_SEARCH_PROPERTIES

    return ROUTE_ASK_QUESTION
