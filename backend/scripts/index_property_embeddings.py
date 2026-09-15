import argparse

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.property import Property
from app.models.property_embedding import PropertyEmbedding
from app.services.embedding_service import EmbeddingService
from app.services.property_document_service import (
    PropertyDocumentService,
)


DEFAULT_BATCH_SIZE = 100
EMBEDDING_DIMENSION = 384


def index_embeddings(
        limit: int | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
) -> None:
    db = SessionLocal()

    document_service = PropertyDocumentService()
    embedding_service = EmbeddingService()

    indexed = 0
    errors = 0

    try:
        print("Iniciando indexação de embeddings...")
        print(f"Tamanho do lote: {batch_size}")

        if limit is not None:
            print(f"Limite máximo: {limit}")

        while True:
            if limit is not None:
                remaining = limit - indexed - errors

                if remaining <= 0:
                    break

                current_batch_size = min(
                    batch_size,
                    remaining,
                )
            else:
                current_batch_size = batch_size

            statement = (
                select(Property)
                .outerjoin(
                    PropertyEmbedding,
                    PropertyEmbedding.property_id
                    == Property.id,
                    )
                .where(
                    PropertyEmbedding.id.is_(None),
                    Property.available.is_(True),
                )
                .order_by(Property.id)
                .limit(current_batch_size)
            )

            properties = list(
                db.execute(statement)
                .scalars()
                .all()
            )

            if not properties:
                break

            print()
            print(
                f"Lote encontrado: "
                f"{len(properties)} imóveis"
            )

            batch_embeddings = []

            for property_ in properties:
                try:
                    content = (
                        document_service.build_document(
                            property_
                        )
                    )

                    embedding = (
                        embedding_service.embed_document(
                            content
                        )
                    )

                    if len(embedding) != EMBEDDING_DIMENSION:
                        raise ValueError(
                            "Embedding com dimensão inválida: "
                            f"{len(embedding)}"
                        )

                    property_embedding = PropertyEmbedding(
                        property_id=property_.id,
                        content=content,
                        embedding=embedding,
                        embedding_model=(
                            EmbeddingService.MODEL_NAME
                        ),
                    )

                    batch_embeddings.append(
                        property_embedding
                    )

                except Exception as error:
                    errors += 1

                    print(
                        f"[ERRO] Property "
                        f"{property_.id}: {error}"
                    )

            if batch_embeddings:
                try:
                    db.add_all(batch_embeddings)
                    db.commit()

                    indexed += len(
                        batch_embeddings
                    )

                    print(
                        f"[OK] Lote salvo. "
                        f"Total indexado: {indexed}"
                    )

                except Exception as error:
                    db.rollback()

                    errors += len(
                        batch_embeddings
                    )

                    print(
                        "[ERRO] Falha ao salvar lote: "
                        f"{error}"
                    )

                    # Tenta salvar individualmente para
                    # identificar registros problemáticos.
                    for property_embedding in batch_embeddings:
                        try:
                            db.add(
                                property_embedding
                            )
                            db.commit()

                            indexed += 1
                            errors -= 1

                        except Exception as item_error:
                            db.rollback()

                            print(
                                "[ERRO] Property "
                                f"{property_embedding.property_id}: "
                                f"{item_error}"
                            )

            db.expunge_all()

        print()
        print("=" * 50)
        print("Indexação concluída.")
        print(f"Indexados: {indexed}")
        print(f"Erros: {errors}")
        print("=" * 50)

    finally:
        db.close()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Gera embeddings para imóveis ainda "
            "não indexados."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Quantidade máxima de imóveis "
            "a serem indexados."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=(
            "Quantidade de imóveis processados "
            "por lote."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    index_embeddings(
        limit=args.limit,
        batch_size=args.batch_size,
    )