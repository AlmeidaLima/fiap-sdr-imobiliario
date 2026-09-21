from app.agents.routing import (
    ROUTE_ASK_QUESTION,
    ROUTE_SEARCH_PROPERTIES,
    route_after_qualification,
)
from app.schemas.conversation import ConversationQualification


def test_route_after_qualification_asks_question_when_not_qualified():
    state = {
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
        "qualification": ConversationQualification(
            qualified=True,
            missing_fields=[],
            next_question=None,
        )
    }

    result = route_after_qualification(state)

    assert result == ROUTE_SEARCH_PROPERTIES