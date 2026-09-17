import re
from decimal import Decimal

from app.schemas.property_search_intent import (
    PropertySearchIntent,
)


class PropertySearchIntentService:

    def parse(
            self,
            message: str,
    ) -> PropertySearchIntent:

        normalized_message = self._normalize_text(
            message
        )

        return PropertySearchIntent(
            semantic_query=message.strip(),
            neighborhood=self._extract_neighborhood(
                normalized_message
            ),
            max_price=self._extract_max_price(
                normalized_message
            ),
            min_bedrooms=self._extract_min_bedrooms(
                normalized_message
            ),
            min_bathrooms=self._extract_min_bathrooms(
                normalized_message
            ),
            min_parking_spaces=(
                self._extract_min_parking_spaces(
                    normalized_message
                )
            ),
            min_usable_area=self._extract_min_usable_area(
                normalized_message
            ),
        )

    @staticmethod
    def _normalize_text(
            value: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    @staticmethod
    def _extract_neighborhood(
            message: str,
    ) -> str | None:

        if re.search(
                r"\bna\s+verdade\b",
                message,
                flags=re.IGNORECASE,
        ):
            message = re.sub(
                r"\bna\s+verdade\b",
                "",
                message,
                flags=re.IGNORECASE,
            ).strip()

        patterns = [
            # Ex.: "no Boa Vista com 3 quartos"
            r"\b(?:no|na)\s+([a-záàâãéêíóôõúç ]+?)(?=\s+com\b)",

            # Ex.: "no Boa Vista até 700 mil"
            r"\b(?:no|na)\s+([a-záàâãéêíóôõúç ]+?)(?=\s+(?:até|ate)\b)",

            # Ex.: "no Boa Vista"
            r"\b(?:no|na)\s+([a-záàâãéêíóôõúç ]+?)$",

            # Ex.: "em Boa Vista com 3 quartos"
            r"\bem\s+([a-záàâãéêíóôõúç ]+?)(?=\s+com\b)",

            # Ex.: "em Boa Vista até 700 mil"
            r"\bem\s+([a-záàâãéêíóôõúç ]+?)(?=\s+(?:até|ate)\b)",

            # Ex.: "em Boa Vista"
            r"\bem\s+([a-záàâãéêíóôõúç ]+?)$",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip().title()

        return None

    @staticmethod
    def _extract_max_price(
            message: str,
    ) -> Decimal | None:

        patterns = [
            r"(?:até|ate)\s+(?:r\$\s*)?([\d.,]+)\s*mil",
            r"(?:até|ate)\s+(?:r\$\s*)?([\d.,]+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1)

            if "mil" in match.group(0).lower():
                numeric_value = Decimal(
                    value.replace(".", "").replace(",", ".")
                )

                return numeric_value * 1000

            return Decimal(
                value.replace(".", "").replace(",", ".")
            )

        return None

    @staticmethod
    def _extract_min_bedrooms(
            message: str,
    ) -> int | None:

        match = re.search(
            r"(\d+)\s+quartos?",
            message,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _extract_min_bathrooms(
            message: str,
    ) -> int | None:

        match = re.search(
            r"(\d+)\s+banheiros?",
            message,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _extract_min_parking_spaces(
            message: str,
    ) -> int | None:

        match = re.search(
            r"(\d+)\s+vagas?",
            message,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _extract_min_usable_area(
            message: str,
    ) -> int | None:

        patterns = [
            r"(\d+)\s*(?:m²|m2|metros quadrados)",
            r"(?:pelo menos|mínimo|minimo)\s+(\d+)\s*metros",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if match:
                return int(match.group(1))

        return None

def test_parse_does_not_interpret_na_verdade_as_neighborhood():
    service = PropertySearchIntentService()

    intent = service.parse(
        "Na verdade pode ser até 800 mil"
    )

    assert intent.neighborhood is None
    assert intent.max_price == Decimal("800000")