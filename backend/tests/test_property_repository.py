from decimal import Decimal

from app.database.property_repository import PropertyRepository
from app.database.session import SessionLocal
from app.models.property import Property

TEST_NEIGHBORHOOD = "__TEST_PROPERTY_FILTER__"

def test_property_repository_save_and_find_by_id():
    db = SessionLocal()

    try:
        repository = PropertyRepository(db)

        property_ = Property(
            external_id="test-repository-save-001",
            title="Apartamento de teste",
            description="Imóvel criado para teste automatizado.",
            usable_area=80,
            total_area=Decimal("100.00"),
            suites=1,
            bathrooms=2,
            bedrooms=3,
            parking_spaces=2,
            amenities=["elevador", "academia"],
            zip_code="80000000",
            longitude=None,
            latitude=None,
            street="Rua de Teste",
            neighborhood=TEST_NEIGHBORHOOD,
            pois=["mercado", "farmácia"],
            yearly_iptu=Decimal("1200.00"),
            monthly_condo_fee=Decimal("500.00"),
            price=Decimal("650000.00"),
            source="test",
            available=True,
        )

        saved = repository.save(property_)

        found = repository.find_by_id(saved.id)

        assert saved.id is not None
        assert found is not None
        assert found.id == saved.id
        assert found.title == "Apartamento de teste"
        assert found.price == Decimal("650000.00")

    finally:
        if "saved" in locals() and saved.id is not None:
            property_to_delete = db.get(Property, saved.id)

            if property_to_delete is not None:
                db.delete(property_to_delete)
                db.commit()

        db.close()


def test_property_repository_find_by_filters():
    db = SessionLocal()
    created_properties = []

    try:
        repository = PropertyRepository(db)

        property_1 = Property(
            external_id="test-repository-filter-001",
            title="Apartamento 1",
            description="Teste de filtro",
            usable_area=80,
            total_area=Decimal("100.00"),
            suites=1,
            bathrooms=2,
            bedrooms=3,
            parking_spaces=2,
            amenities=[],
            zip_code="80000001",
            street="Rua A",
            neighborhood=TEST_NEIGHBORHOOD,
            pois=[],
            price=Decimal("600000.00"),
            source="test",
            available=True,
        )

        property_2 = Property(
            external_id="test-repository-filter-002",
            title="Apartamento 2",
            description="Teste de filtro",
            usable_area=60,
            total_area=Decimal("75.00"),
            suites=0,
            bathrooms=1,
            bedrooms=2,
            parking_spaces=1,
            amenities=[],
            zip_code="80000002",
            street="Rua B",
            neighborhood=TEST_NEIGHBORHOOD,
            pois=[],
            price=Decimal("450000.00"),
            source="test",
            available=True,
        )

        repository.save(property_1)
        repository.save(property_2)

        created_properties.extend(
            [property_1, property_2]
        )

        results = repository.find_by_filters(
            neighborhood=TEST_NEIGHBORHOOD,
            max_price=Decimal("500000.00"),
            min_bedrooms=2,
        )

        assert len(results) == 1
        assert results[0].id == property_2.id
        assert results[0].price == Decimal("450000.00")

    finally:
        for property_ in created_properties:
            persisted = db.get(Property, property_.id)

            if persisted is not None:
                db.delete(persisted)

        db.commit()
        db.close()