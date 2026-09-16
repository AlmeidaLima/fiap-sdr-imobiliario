from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property import Property
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

    def search_similar_with_filters(
            self,
            query_embedding: list[float],
            neighborhood: str | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            min_bedrooms: int | None = None,
            min_bathrooms: int | None = None,
            min_parking_spaces: int | None = None,
            min_usable_area: int | None = None,
            available: bool = True,
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
            .join(
                Property,
                Property.id == PropertyEmbedding.property_id,
                )
            .where(
                Property.available.is_(available)
            )
        )

        if neighborhood:
            statement = statement.where(
                Property.neighborhood.ilike(
                    f"%{neighborhood}%"
                )
            )

        if min_price is not None:
            statement = statement.where(
                Property.price >= min_price
            )

        if max_price is not None:
            statement = statement.where(
                Property.price <= max_price
            )

        if min_bedrooms is not None:
            statement = statement.where(
                Property.bedrooms >= min_bedrooms
            )

        if min_bathrooms is not None:
            statement = statement.where(
                Property.bathrooms >= min_bathrooms
            )

        if min_parking_spaces is not None:
            statement = statement.where(
                Property.parking_spaces >= min_parking_spaces
            )

        if min_usable_area is not None:
            statement = statement.where(
                Property.usable_area >= min_usable_area
            )

        statement = (
            statement
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