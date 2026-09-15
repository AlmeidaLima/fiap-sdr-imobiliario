from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property_embedding import PropertyEmbedding


class PropertyEmbeddingRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(
            self,
            property_embedding: PropertyEmbedding,
    ) -> PropertyEmbedding:
        self.db.add(property_embedding)
        self.db.commit()
        self.db.refresh(property_embedding)

        return property_embedding

    def find_by_property_id(
            self,
            property_id: int,
    ) -> PropertyEmbedding | None:
        statement = select(PropertyEmbedding).where(
            PropertyEmbedding.property_id == property_id
        )

        result = self.db.execute(statement)

        return result.scalar_one_or_none()

    def search_similar(
            self,
            query_embedding: list[float],
            limit: int = 5,
    ) -> list[tuple[PropertyEmbedding, float]]:
        distance = (
            PropertyEmbedding.embedding.cosine_distance(
                query_embedding
            )
        )

        statement = (
            select(
                PropertyEmbedding,
                distance.label("distance"),
            )
            .order_by(distance)
            .limit(limit)
        )

        rows = self.db.execute(statement).all()

        return [
            (
                property_embedding,
                1.0 - float(distance_value),
            )
            for property_embedding, distance_value in rows
        ]