from decimal import Decimal

import pytest

from app.schemas.conversation import ConversationState
from app.services.lead_score_service import LeadScoreService


def calculate(**state_data):
    state = ConversationState(
        conversation_id="lead-score-test",
        **state_data,
    )
    return LeadScoreService().calculate(state)


def test_empty_state_is_cold_with_zero_score():
    result = calculate()
    assert result.score == 0
    assert result.classification == "FRIO"


def test_identified_intent_adds_twenty_points():
    result = calculate(commercial_intent="COMPRA")
    assert result.score == 20
    assert result.classification == "FRIO"


def test_undefined_intent_does_not_score():
    assert calculate(commercial_intent="INDEFINIDO").score == 0


def test_intent_and_budget_add_forty_points():
    result = calculate(
        commercial_intent="ALUGUEL",
        max_price=Decimal("3000"),
    )
    assert result.score == 40
    assert result.classification == "MORNO"


@pytest.mark.parametrize(
    ("budget", "expected_score"),
    [
        ({"min_price": Decimal("2000")}, 20),
        ({"max_price": Decimal("3000")}, 20),
        (
            {
                "min_price": Decimal("2000"),
                "max_price": Decimal("3000"),
            },
            20,
        ),
    ],
)
def test_informed_budget_adds_twenty_points_only_once(
        budget,
        expected_score,
):
    assert calculate(**budget).score == expected_score


def test_defined_region_adds_ten_points():
    assert calculate(neighborhood="Boa Vista").score == 10


@pytest.mark.parametrize(
    ("urgency_days", "expected_score"),
    [
        (30, 25),
        (31, 15),
        (90, 15),
        (91, 0),
    ],
)
def test_urgency_score_boundaries(urgency_days, expected_score):
    assert calculate(urgency_days=urgency_days).score == expected_score


def test_accepted_meeting_or_visit_adds_twenty_five_points():
    assert calculate(accepted_meeting_or_visit=True).score == 25


def test_maximum_scenario_is_hot_with_one_hundred_points():
    result = calculate(
        commercial_intent="INVESTIMENTO",
        max_price=Decimal("700000"),
        neighborhood="Boa Vista",
        urgency_days=15,
        accepted_meeting_or_visit=True,
    )
    assert result.score == 100
    assert result.classification == "QUENTE"


def test_calculate_does_not_modify_conversation_state():
    state = ConversationState(
        conversation_id="lead-score-pure-service",
        commercial_intent="COMPRA",
        max_price=Decimal("700000"),
        neighborhood="Boa Vista",
        urgency_days=30,
        accepted_meeting_or_visit=True,
        lead_score=0,
        lead_classification="FRIO",
    )

    result = LeadScoreService().calculate(state)

    assert result.score == 100
    assert result.classification == "QUENTE"
    assert state.lead_score == 0
    assert state.lead_classification == "FRIO"


@pytest.mark.parametrize(
    ("score", "classification"),
    [(39, "FRIO"), (40, "MORNO"), (69, "MORNO"), (70, "QUENTE")],
)
def test_classification_boundaries(score, classification):
    assert LeadScoreService.classify(score) == classification


def test_missing_optional_fields_do_not_raise_error():
    result = calculate(commercial_intent=None, urgency_days=None)
    assert result.score == 0
    assert result.classification == "FRIO"
