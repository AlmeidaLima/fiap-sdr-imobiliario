import re
import unicodedata
from dataclasses import dataclass
from typing import Literal


CommercialIntent = Literal[
    "COMPRA",
    "ALUGUEL",
    "INVESTIMENTO",
    "INDEFINIDO",
]


@dataclass(frozen=True)
class CommercialQualification:
    commercial_intent: CommercialIntent = "INDEFINIDO"
    urgency_days: int | None = None
    accepted_meeting_or_visit: bool = False


class CommercialQualificationService:

    INTENT_PATTERNS = (
        (
            "INVESTIMENTO",
            r"(?<!nao )\b(?:quero|procuro|pretendo|desejo|estou procurando)\b"
            r"[^.!?]*\b(?:investimento|investir)\b",
        ),
        (
            "ALUGUEL",
            r"(?<!nao )\b(?:quero|procuro|pretendo|desejo|estou procurando)\b"
            r"[^.!?]*\b(?:alugar|aluguel|locar|locacao)\b",
        ),
        (
            "COMPRA",
            r"(?<!nao )\b(?:quero|procuro|pretendo|desejo|estou procurando)\b"
            r"[^.!?]*\b(?:comprar|compra)\b",
        ),
    )

    URGENCY_PATTERN = re.compile(
        r"\b(?:em|nos? proximos?|daqui a)\s+"
        r"(?:ate\s+)?"
        r"(\d+)\s+"
        r"(dias?|mes|meses)\b"
    )

    def extract(
            self,
            message: str,
    ) -> CommercialQualification:
        normalized_message = self._normalize_text(message)

        return CommercialQualification(
            commercial_intent=self._extract_commercial_intent(
                normalized_message
            ),
            urgency_days=self._extract_urgency_days(
                normalized_message
            ),
        )

    @classmethod
    def _extract_commercial_intent(
            cls,
            message: str,
    ) -> CommercialIntent:
        for intent, pattern in cls.INTENT_PATTERNS:
            if re.search(pattern, message):
                return intent

        return "INDEFINIDO"

    @classmethod
    def _extract_urgency_days(
            cls,
            message: str,
    ) -> int | None:
        match = cls.URGENCY_PATTERN.search(message)

        if not match:
            return None

        quantity = int(match.group(1))
        unit = match.group(2)

        if quantity < 1:
            return None

        if unit.startswith("mes"):
            return quantity * 30

        return quantity

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        without_accents = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        return re.sub(
            r"\s+",
            " ",
            without_accents.strip().lower(),
        )
