import ast
import hashlib
import json
import math

from decimal import Decimal
from pathlib import Path

import pandas as pd

from app.database.session import SessionLocal
from app.models.property import Property


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CSV_PATH = Path(
    "/app/data/raw/curitiba_apartment_real_estate_data.csv"
)

SOURCE_NAME = "curitiba_kaggle"


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def is_null(value) -> bool:
    return value is None or (
            isinstance(value, float) and math.isnan(value)
    )


def to_optional_int(value) -> int | None:
    if is_null(value):
        return None

    return int(value)


def to_optional_decimal(value) -> Decimal | None:
    if is_null(value):
        return None

    return Decimal(str(value))


def to_optional_string(value) -> str | None:
    if is_null(value):
        return None

    value = str(value).strip()

    return value or None


def to_zip_code(value) -> str:
    if is_null(value):
        return ""

    return str(int(value)).zfill(8)


def parse_list(value) -> list:
    if is_null(value):
        return []

    if isinstance(value, list):
        return value

    try:
        parsed = ast.literal_eval(str(value))

        if isinstance(parsed, list):
            return parsed

    except (ValueError, SyntaxError):
        pass

    return []


# ============================================================
# EXTERNAL ID
# ============================================================

def normalize_hash_value(value) -> str:
    """
    Normaliza os valores antes da geração do hash.

    Isso evita diferenças desnecessárias na representação
    dos dados, principalmente Decimal, listas e dicionários.
    """

    if value is None:
        return ""

    if isinstance(value, Decimal):
        return format(value.normalize(), "f")

    if isinstance(value, (list, dict)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    return str(value).strip()


def generate_external_id(property_: Property) -> str:
    """
    Gera um identificador determinístico SHA-256 utilizando
    os dados relevantes do imóvel.

    O mesmo imóvel com os mesmos dados sempre produzirá
    o mesmo external_id.
    """

    raw_value = "|".join(
        [
            normalize_hash_value(property_.source),
            normalize_hash_value(property_.title),
            normalize_hash_value(property_.description),
            normalize_hash_value(property_.usable_area),
            normalize_hash_value(property_.total_area),
            normalize_hash_value(property_.suites),
            normalize_hash_value(property_.bathrooms),
            normalize_hash_value(property_.bedrooms),
            normalize_hash_value(property_.parking_spaces),
            normalize_hash_value(property_.amenities),
            normalize_hash_value(property_.zip_code),
            normalize_hash_value(property_.longitude),
            normalize_hash_value(property_.latitude),
            normalize_hash_value(property_.street),
            normalize_hash_value(property_.neighborhood),
            normalize_hash_value(property_.pois),
            normalize_hash_value(property_.yearly_iptu),
            normalize_hash_value(property_.monthly_condo_fee),
            normalize_hash_value(property_.price),
        ]
    )

    return hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()


# ============================================================
# CONVERSÃO CSV -> PROPERTY
# ============================================================

def row_to_property(row) -> Property:
    property_ = Property(
        title=to_optional_string(row["title"]),
        description=to_optional_string(row["description"]),

        usable_area=int(row["usableAreas"]),
        total_area=to_optional_decimal(row["totalAreas"]),

        suites=to_optional_int(row["suites"]),
        bathrooms=int(row["bathrooms"]),
        bedrooms=int(row["bedrooms"]),
        parking_spaces=to_optional_int(row["parkingSpaces"]),

        amenities=parse_list(row["amenities"]),

        zip_code=to_zip_code(row["zipCode"]),

        longitude=to_optional_decimal(row["lon"]),
        latitude=to_optional_decimal(row["lat"]),

        street=to_optional_string(row["street"]),
        neighborhood=str(row["neighborhood"]).strip(),

        pois=parse_list(row["poisList"]),

        yearly_iptu=to_optional_decimal(row["yearlyIptu"]),
        monthly_condo_fee=to_optional_decimal(
            row["monthlyCondoFee"]
        ),

        price=Decimal(str(row["price"])),

        source=SOURCE_NAME,
        available=True,
    )

    property_.external_id = generate_external_id(property_)

    return property_


# ============================================================
# DRY RUN
# ============================================================

def dry_run(limit: int = 5) -> None:
    """
    Lê algumas linhas do CSV e realiza a transformação
    sem inserir registros no banco.
    """

    dataframe = pd.read_csv(CSV_PATH)

    print(f"Registros no CSV: {len(dataframe)}")
    print(f"Colunas: {list(dataframe.columns)}")
    print()

    for index, row in dataframe.head(limit).iterrows():
        property_ = row_to_property(row)

        print(f"--- Imóvel {index + 1} ---")

        print(
            {
                "external_id": property_.external_id,
                "title": property_.title,
                "usable_area": property_.usable_area,
                "bedrooms": property_.bedrooms,
                "bathrooms": property_.bathrooms,
                "parking_spaces": property_.parking_spaces,
                "neighborhood": property_.neighborhood,
                "price": property_.price,
                "amenities": property_.amenities,
                "pois": property_.pois,
            }
        )

        print()


# ============================================================
# VALIDAÇÃO DOS EXTERNAL IDS
# ============================================================

def validate_external_ids() -> None:
    """
    Calcula os external_ids dos imóveis existentes no banco
    sem persistir nenhuma alteração.

    Serve para verificar se existem dois registros que
    produziriam o mesmo external_id.
    """

    db = SessionLocal()

    try:
        properties = (
            db.query(Property)
            .order_by(Property.id)
            .all()
        )

        external_ids = {}
        duplicates = []

        for property_ in properties:
            external_id = generate_external_id(property_)

            if external_id in external_ids:
                duplicates.append(
                    {
                        "external_id": external_id,
                        "first_id": external_ids[external_id],
                        "duplicate_id": property_.id,
                        "title": property_.title,
                        "neighborhood": property_.neighborhood,
                        "price": property_.price,
                    }
                )

            else:
                external_ids[external_id] = property_.id

        print(
            f"Total de imóveis: {len(properties)}"
        )

        print(
            f"External IDs únicos: {len(external_ids)}"
        )

        print(
            f"Duplicidades: {len(duplicates)}"
        )

        if duplicates:
            print()
            print("Primeiras duplicidades encontradas:")

            for duplicate in duplicates[:20]:
                print(duplicate)

    finally:
        db.close()


# ============================================================
# BACKFILL
# ============================================================

def backfill_external_ids() -> None:
    """
    Preenche external_id apenas nos imóveis que ainda
    possuem external_id NULL.

    Esta função NÃO cria novos imóveis.
    """

    db = SessionLocal()

    updated = 0

    try:
        properties = (
            db.query(Property)
            .filter(Property.external_id.is_(None))
            .order_by(Property.id)
            .all()
        )

        print(
            f"Imóveis sem external_id: {len(properties)}"
        )

        for property_ in properties:
            property_.external_id = generate_external_id(
                property_
            )

            updated += 1

        db.commit()

        print(
            f"Backfill concluído: "
            f"{updated} imóveis atualizados."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# IMPORTAÇÃO
# ============================================================

def import_properties() -> None:
    """
    Importa imóveis do CSV ignorando registros cujo
    external_id já existe no banco.

    ATENÇÃO:
    Esta função só deve ser utilizada depois da validação
    dos external_ids e conclusão do backfill.
    """

    dataframe = pd.read_csv(CSV_PATH)

    db = SessionLocal()

    imported = 0
    skipped = 0

    try:
        existing_ids = {
            external_id
            for (external_id,) in db.query(
                Property.external_id
            )
            .filter(
                Property.external_id.is_not(None)
            )
            .all()
        }

        properties_to_insert = []

        for _, row in dataframe.iterrows():
            property_ = row_to_property(row)

            if property_.external_id in existing_ids:
                skipped += 1
                continue

            properties_to_insert.append(property_)

            # Importante:
            # adicionamos imediatamente ao conjunto para
            # evitar duplicidades dentro do próprio CSV.
            existing_ids.add(property_.external_id)

        if properties_to_insert:
            db.add_all(properties_to_insert)
            db.commit()

        imported = len(properties_to_insert)

        print(
            "Importação concluída: "
            f"{imported} imóveis importados, "
            f"{skipped} ignorados."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# EXECUÇÃO
# ============================================================
if __name__ == "__main__":
    import_properties()