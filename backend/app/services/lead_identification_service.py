import re


class LeadIdentificationService:

    NAME_TERMINATOR = (
        r"(?=\s+e\s+(?:estou|quero|procuro|preciso)\b|[,.;!?]|$)"
    )

    NAME_PATTERNS = [
        r"\bmeu nome é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)"
        + NAME_TERMINATOR,
        r"\bmeu nome e\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)"
        + NAME_TERMINATOR,
        r"\bsou\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)"
        + NAME_TERMINATOR,
        r"\bpode me chamar de\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)"
        + NAME_TERMINATOR,
    ]

    def extract_name(
            self,
            message: str,
    ) -> str | None:
        text = message.strip()

        for pattern in self.NAME_PATTERNS:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return self._normalize_name(
                    match.group(1)
                )

        return None

    @staticmethod
    def _normalize_name(
            name: str,
    ) -> str:
        return " ".join(
            word.capitalize()
            for word in name.split()
        )
