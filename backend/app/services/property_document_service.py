import html
import re

from app.models.property import Property


AMENITY_TRANSLATIONS = {
    "BARBECUE_GRILL": "churrasqueira",
    "ELEVATOR": "elevador",
    "GATED_COMMUNITY": "condomínio fechado",
    "GYM": "academia",
    "PETS_ALLOWED": "aceita pets",
    "GOURMET_BALCONY": "varanda gourmet",
    "PARTY_HALL": "salão de festas",
    "AMERICAN_KITCHEN": "cozinha americana",
    "LAUNDRY": "lavanderia",
    "DISABLED_ACCESS": "acessibilidade",
    "ELECTRONIC_GATE": "portão eletrônico",
    "POOL": "piscina",
    "FURNISHED": "mobiliado",
    "GOURMET_SPACE": "espaço gourmet",
    "AIR_CONDITIONING": "ar-condicionado",
    "GARDEN": "jardim",
    "PLAYGROUND": "playground",
    "SPORTS_COURT": "quadra esportiva",
    "BICYCLES_PLACE": "bicicletário",
    "CONCIERGE_24H": "portaria 24 horas",
    "CINEMA": "cinema",
    "GAMES_ROOM": "sala de jogos",
    "CLOSET": "closet",
    "INTERCOM": "interfone",
}


POI_PREFIXES = {
    "BS": "ponto de ônibus",
    "TS": "transporte",
    "CS": "comércio",
    "PH": "farmácia",
    "CH": "saúde",
    "VP": "pet shop ou veterinário",
}


class PropertyDocumentService:

    MAX_DOCUMENT_LENGTH = 4000

    @staticmethod
    def _clean_text(
            value: str | None,
    ) -> str | None:
        if not value:
            return None

        # Converte entidades HTML.
        # Exemplo: "&amp;" -> "&"
        text = html.unescape(value)

        # Substitui <br>, <br/> e <br /> por espaço.
        text = re.sub(
            r"<br\s*/?>",
            " ",
            text,
            flags=re.IGNORECASE,
        )

        # Remove as demais tags HTML.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # Normaliza espaços, tabs e quebras de linha.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # Remove espaços indevidos antes da pontuação.
        # Exemplo:
        # "churrasqueira ." -> "churrasqueira."
        text = re.sub(
            r"\s+([.,;:!?])",
            r"\1",
            text,
        )

        return text.strip()

    def build_document(
            self,
            property_: Property,
    ) -> str:
        parts = []

        self._append(
            parts,
            "Título",
            self._clean_text(property_.title),
        )

        self._append(
            parts,
            "Bairro",
            property_.neighborhood,
        )

        self._append(
            parts,
            "Rua",
            property_.street,
        )

        self._append(
            parts,
            "CEP",
            property_.zip_code,
        )

        self._append(
            parts,
            "Área útil",
            self._format_area(
                property_.usable_area
            ),
        )

        self._append(
            parts,
            "Área total",
            self._format_area(
                property_.total_area
            ),
        )

        self._append(
            parts,
            "Quartos",
            property_.bedrooms,
        )

        self._append(
            parts,
            "Suítes",
            property_.suites,
        )

        self._append(
            parts,
            "Banheiros",
            property_.bathrooms,
        )

        self._append(
            parts,
            "Vagas",
            property_.parking_spaces,
        )

        self._append(
            parts,
            "Preço",
            self._format_currency(
                property_.price
            ),
        )

        self._append(
            parts,
            "Condomínio mensal",
            self._format_currency(
                property_.monthly_condo_fee
            ),
        )

        self._append(
            parts,
            "IPTU anual",
            self._format_currency(
                property_.yearly_iptu
            ),
        )

        amenities = self._normalize_amenities(
            property_.amenities
        )

        if amenities:
            parts.append(
                "Comodidades: "
                + ", ".join(amenities)
                + "."
            )

        pois = self._normalize_pois(
            property_.pois
        )

        if pois:
            parts.append(
                "Pontos de interesse: "
                + ", ".join(pois)
                + "."
            )

        description = self._clean_text(
            property_.description
        )

        if description:
            parts.append(
                "Descrição: "
                + description
            )

        document = "\n".join(parts)

        return document[
            : self.MAX_DOCUMENT_LENGTH
        ]

    @staticmethod
    def _append(
            parts: list[str],
            label: str,
            value,
    ) -> None:
        if value is None:
            return

        if value == "":
            return

        parts.append(
            f"{label}: {value}."
        )

    @staticmethod
    def _format_area(value):
        if value is None:
            return None

        return f"{value} m²"

    @staticmethod
    def _format_currency(value):
        if value is None:
            return None

        return f"R$ {value}"

    @staticmethod
    def _normalize_amenities(
            amenities: list | None,
    ) -> list[str]:
        if not amenities:
            return []

        return [
            AMENITY_TRANSLATIONS.get(
                amenity,
                str(amenity)
                .replace("_", " ")
                .lower(),
                )
            for amenity in amenities
        ]

    @staticmethod
    def _normalize_pois(
            pois: list | None,
    ) -> list[str]:
        if not pois:
            return []

        normalized = []

        for poi in pois:
            value = str(poi)

            if ":" not in value:
                normalized.append(value)
                continue

            prefix, description = value.split(
                ":",
                1,
            )

            category = POI_PREFIXES.get(
                prefix,
                prefix,
            )

            normalized.append(
                f"{category}: {description}"
            )

        return normalized