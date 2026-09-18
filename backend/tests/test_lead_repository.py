from app.database.lead_repository import LeadRepository
from app.database.session import SessionLocal


def test_create_lead():
    db = SessionLocal()

    try:
        repository = LeadRepository(db)

        lead = repository.create(
            name="Rafael Teste",
            phone="61999999999",
            email="rafael.teste@example.com",
        )

        assert lead.id is not None
        assert lead.name == "Rafael Teste"
        assert lead.phone == "61999999999"
        assert lead.email == "rafael.teste@example.com"
        assert lead.status == "new"

    finally:
        db.close()


def test_find_lead_by_id():
    db = SessionLocal()

    try:
        repository = LeadRepository(db)

        created = repository.create(
            name="Cliente Teste",
            phone="61888888888",
            email="cliente.teste@example.com",
        )

        found = repository.find_by_id(
            created.id
        )

        assert found is not None
        assert found.id == created.id
        assert found.name == "Cliente Teste"
        assert found.phone == "61888888888"
        assert found.email == "cliente.teste@example.com"

    finally:
        db.close()