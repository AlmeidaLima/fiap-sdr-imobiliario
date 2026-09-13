from decimal import Decimal

from app.database.property_repository import PropertyRepository
from app.models.property import Property


class PropertyService:

    def __init__(self, repository: PropertyRepository):
        self.repository = repository

    def create(self, property_: Property) -> Property:
        return self.repository.save(property_)

    def get_by_id(self, property_id: int) -> Property | None:
        return self.repository.find_by_id(property_id)

    def list_all(self) -> list[Property]:
        return self.repository.find_all()

    def search(
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
        return self.repository.find_by_filters(
            neighborhood=neighborhood,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            min_bathrooms=min_bathrooms,
            min_parking_spaces=min_parking_spaces,
            min_usable_area=min_usable_area,
            available=available,
            limit=limit,
        )