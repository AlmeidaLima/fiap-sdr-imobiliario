from typing import Literal

from app.schemas.conversation import ConversationState, LeadScoreResult


LeadClassification = Literal["FRIO", "MORNO", "QUENTE"]


class LeadScoreService:

    IDENTIFIED_INTENT_SCORE = 20
    INFORMED_BUDGET_SCORE = 20
    DEFINED_REGION_SCORE = 10
    URGENCY_WITHIN_30_DAYS_SCORE = 25
    URGENCY_WITHIN_90_DAYS_SCORE = 15
    ACCEPTED_MEETING_OR_VISIT_SCORE = 25

    IDENTIFIED_INTENTS = {
        "COMPRA",
        "ALUGUEL",
        "INVESTIMENTO",
    }

    def calculate(
            self,
            state: ConversationState,
    ) -> LeadScoreResult:
        score = 0

        if state.commercial_intent in self.IDENTIFIED_INTENTS:
            score += self.IDENTIFIED_INTENT_SCORE

        if state.min_price is not None or state.max_price is not None:
            score += self.INFORMED_BUDGET_SCORE

        if state.neighborhood and state.neighborhood.strip():
            score += self.DEFINED_REGION_SCORE

        if state.urgency_days is not None:
            if state.urgency_days <= 30:
                score += self.URGENCY_WITHIN_30_DAYS_SCORE
            elif state.urgency_days <= 90:
                score += self.URGENCY_WITHIN_90_DAYS_SCORE

        if state.accepted_meeting_or_visit:
            score += self.ACCEPTED_MEETING_OR_VISIT_SCORE

        score = min(score, 100)

        return LeadScoreResult(
            score=score,
            classification=self.classify(score),
        )

    @staticmethod
    def classify(score: int) -> LeadClassification:
        if not 0 <= score <= 100:
            raise ValueError("Lead score must be between 0 and 100.")

        if score >= 70:
            return "QUENTE"

        if score >= 40:
            return "MORNO"

        return "FRIO"
