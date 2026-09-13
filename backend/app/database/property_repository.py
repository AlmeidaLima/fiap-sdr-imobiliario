from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property import Property


class PropertyRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(self, property_: Property) -> Property:
        self.db.add(property_)
        self.db.commit()
        self.db.refresh(property_)

        return property_

    def find_by_id(self, property_id: int) -> Property | None:
        return self.db.get(Property, property_id)

    def find_all(self) -> list[Property]:
        statement = select(Property).order_by(Property.id)

        result = self.db.execute(statement)

        return list(result.scalars().all())

    def find_by_filters(
            self,
            neighborhood: str | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            min_bedrooms: int | None = None,
            min_bathrooms: int | None = None,
            min_parking_spaces: int | None = None,
            min_usable_area: int | None = None,
            available: bool = True,
            limit: int = 20,
    ) -> list[Property]:
        statement = select(Property)

        if neighborhood is not None:
            statement = statement.where(
                Property.neighborhood.ilike(neighborhood)
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

        statement = statement.where(
            Property.available == available
        )

        statement = statement.order_by(
            Property.price.asc(),
            Property.id.asc(),
        )

        statement = statement.limit(limit)

        result = self.db.execute(statement)

        return list(result.scalars().all())