from decimal import Decimal

from app.models.property import Property
from app.services.property_document_service import (
    PropertyDocumentService,
)


def test_build_property_document():
    property_ = Property(
        external_id="test-document-001",
        title="Apartamento no Boa Vista",
        description="Apartamento ensolarado e bem localizado.",
        usable_area=77,
        total_area=Decimal("90.00"),
        suites=1,
        bathrooms=2,
        bedrooms=3,
        parking_spaces=1,
        amenities=[
            "BARBECUE_GRILL",
            "GYM",
            "PETS_ALLOWED",
        ],
        zip_code="80000000",
        street="Rua de Teste",
        neighborhood="Boa Vista",
        pois=[
            "BS:Estação Tubo",
            "PH:Farmácia Central",
        ],
        yearly_iptu=Decimal("1200.00"),
        monthly_condo_fee=Decimal("500.00"),
        price=Decimal("595000.00"),
        source="test",
        available=True,
    )

    service = PropertyDocumentService()

    document = service.build_document(property_)

    assert "Apartamento no Boa Vista" in document
    assert "Bairro: Boa Vista" in document
    assert "Quartos: 3" in document
    assert "churrasqueira" in document
    assert "academia" in document
    assert "aceita pets" in document
    assert "ponto de ônibus" in document
    assert "farmácia" in document
    assert "Apartamento ensolarado" in document


def test_clean_text_removes_html():
    service = PropertyDocumentService()

    text = (
        "Apartamento reformado.<br>"
        "Próximo ao parque.<br/>"
        "Academia e <strong>churrasqueira</strong>."
    )

    result = service._clean_text(text)

    assert result == (
        "Apartamento reformado. "
        "Próximo ao parque. "
        "Academia e churrasqueira."
    )

    assert "<br>" not in result
    assert "<strong>" not in result


def test_clean_text_normalizes_spaces():
    service = PropertyDocumentService()

    result = service._clean_text(
        "Apartamento   com   academia\n"
        "e churrasqueira."
    )

    assert result == (
        "Apartamento com academia "
        "e churrasqueira."
    )