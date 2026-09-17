from app.schemas.conversation import (
    ConversationQualification,
    ConversationState,
)


class ConversationQualificationService:

    REQUIRED_FIELDS = (
        "neighborhood",
        "max_price",
        "min_bedrooms",
    )

    QUESTIONS = {
        "neighborhood": (
            "Em qual bairro ou região você procura o imóvel?"
        ),
        "max_price": (
            "Qual é o valor máximo que você pretende investir no imóvel?"
        ),
        "min_bedrooms": (
            "Quantos quartos você procura?"
        ),
    }

    def qualify(
            self,
            state: ConversationState,
    ) -> ConversationQualification:

        missing_fields = [
            field
            for field in self.REQUIRED_FIELDS
            if getattr(state, field) is None
        ]

        qualified = len(missing_fields) == 0

        next_question = None

        if missing_fields:
            next_question = self.QUESTIONS[
                missing_fields[0]
            ]

        return ConversationQualification(
            qualified=qualified,
            missing_fields=missing_fields,
            next_question=next_question,
        )