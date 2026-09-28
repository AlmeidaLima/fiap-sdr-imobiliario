from app.agents.routing import (
    ROUTE_APPOINTMENT_FLOW,
    ROUTE_ASK_QUESTION,
    ROUTE_SEARCH_PROPERTIES,
    route_after_qualification,
)
from app.schemas.conversation import ConversationQualification, ConversationState


def test_route_after_qualification_asks_question_when_not_qualified():
    state = {
        "conversation_state": ConversationState(
            conversation_id="routing-unqualified",
        ),
        "qualification": ConversationQualification(
            qualified=False,
            missing_fields=["max_price", "min_bedrooms"],
            next_question="Qual é o valor máximo que você pretende investir no imóvel?",
        )
    }

    result = route_after_qualification(state)

    assert result == ROUTE_ASK_QUESTION


def test_route_after_qualification_searches_when_qualified():
    state = {
        "conversation_state": ConversationState(
            conversation_id="routing-qualified",
        ),
        "qualification": ConversationQualification(
            qualified=True,
            missing_fields=[],
            next_question=None,
        )
    }

    result = route_after_qualification(state)

    assert result == ROUTE_SEARCH_PROPERTIES


def test_route_after_qualification_prioritizes_active_appointment_flow():
    state = {
        "conversation_state": ConversationState(
            conversation_id="routing-appointment",
            presented_property_ids=[10],
            selected_property_id=10,
            appointment_stage="AWAITING_DATE",
        ),
        "qualification": ConversationQualification(
            qualified=True,
            missing_fields=[],
            next_question=None,
        ),
    }

    assert route_after_qualification(state) == ROUTE_APPOINTMENT_FLOW
