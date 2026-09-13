from decimal import Decimal
from unittest.mock import Mock

from app.models.property import Property
from app.services.property_service import PropertyService


def test_property_service_search_delegates_filters_to_repository():
    repository = Mock()

    expected_properties = [
        Property(
            id=1,
            title="Apartamento teste",
            description="Teste",
            usable_area=80,
            bathrooms=2,
            bedrooms=3,
            amenities=[],
            zip_code="80000000",
            neighborhood="Centro",
            pois=[],
            price=Decimal("500000.00"),
            source="test",
            available=True,
        )
    ]

    repository.find_by_filters.return_value = expected_properties

    service = PropertyService(repository)

    result = service.search(
        neighborhood="Centro",
        max_price=Decimal("600000.00"),
        min_bedrooms=3,
        limit=10,
    )

    repository.find_by_filters.assert_called_once_with(
        neighborhood="Centro",
        min_price=None,
        max_price=Decimal("600000.00"),
        min_bedrooms=3,
        min_bathrooms=None,
        min_parking_spaces=None,
        min_usable_area=None,
        available=True,
        limit=10,
    )

    assert result == expected_properties