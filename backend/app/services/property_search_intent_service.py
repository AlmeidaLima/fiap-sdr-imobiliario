
import re
import unicodedata
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

        # Evita interpretar "na verdade" como localização.
        message = re.sub(
            r"\bna\s+verdade\b",
            "",
            message,
            flags=re.IGNORECASE,
        ).strip()

        # Ex.: "no bairro Boa Vista e preciso do imóvel em até 30 dias"
        match = re.search(
            r"\b(?:no|na|em)\s+bairro\s+"
            r"([a-záàâãéêíóôõúç ]+?)"
            r"(?=\s+e\s+(?:preciso|quero|desejo|pretendo)\b"
            r"|\s+(?:com|até|ate)\b"
            r"|[.!?,]|$)",
            message,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip().title()

        patterns = [
            # Ex.: "no Boa Vista com 3 quartos"
            (
                r"\b(?:no|na)\s+"
                r"([a-záàâãéêíóôõúç ]+?)"
                r"(?=\s+com\b)"
            ),

            # Ex.: "no Boa Vista até 700 mil"
            (
                r"\b(?:no|na)\s+"
                r"([a-záàâãéêíóôõúç ]+?)"
                r"(?=\s+(?:até|ate)\b)"
            ),

            # Ex.: "no Boa Vista"
            (
                r"\b(?:no|na)\s+"
                r"([a-záàâãéêíóôõúç ]+?)$"
            ),

            # Ex.: "em Boa Vista com 3 quartos"
            (
                r"\bem\s+"
                r"([a-záàâãéêíóôõúç ]+?)"
                r"(?=\s+com\b)"
            ),

            # Ex.: "em Boa Vista até 700 mil"
            (
                r"\bem\s+"
                r"([a-záàâãéêíóôõúç ]+?)"
                r"(?=\s+(?:até|ate)\b)"
            ),

            # Ex.: "em Boa Vista"
            (
                r"\bem\s+"
                r"([a-záàâãéêíóôõúç ]+?)$"
            ),
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

        # Remove acentos apenas para reconhecer expressões
        # como "orçamento máximo" e "até".
        normalized = unicodedata.normalize(
            "NFKD",
            message,
        )
        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        patterns = [
            # Ex.: "Meu orçamento máximo é de R$ 400.000"
            (
                r"orcamento\s+maximo\s+"
                r"(?:e\s+)?(?:de\s+)?"
                r"r\$\s*([\d.,]+)"
            ),

            # Ex.: "até 700 mil"
            r"\bate\s+(?:r\$\s*)?([\d.,]+)\s*mil\b",

            # Ex.: "até R$ 650.000"
            r"\bate\s+r\$\s*([\d.,]+)",

            # Ex.: "até 550000", mas não "até 30 dias"
            r"\bate\s+([\d.,]+)(?=\s*(?:[.!?,]|$))",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1).rstrip(".,")

            numeric_value = Decimal(
                value.replace(".", "").replace(",", ".")
            )

            if re.search(
                    r"\bmil\b",
                    match.group(0),
                    flags=re.IGNORECASE,
            ):
                return numeric_value * 1000

            return numeric_value

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
            (
                r"(?:pelo menos|mínimo|minimo)\s+"
                r"(\d+)\s*metros"
            ),
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
