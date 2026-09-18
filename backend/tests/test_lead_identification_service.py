from app.services.lead_identification_service import (
    LeadIdentificationService,
)


def test_extract_name_from_meu_nome_e():
    service = LeadIdentificationService()

    name = service.extract_name(
        "Meu nome é Rafael Almeida"
    )

    assert name == "Rafael Almeida"


def test_extract_name_from_sou():
    service = LeadIdentificationService()

    name = service.extract_name(
        "Sou Rafael"
    )

    assert name == "Rafael"


def test_extract_name_from_pode_me_chamar_de():
    service = LeadIdentificationService()

    name = service.extract_name(
        "Pode me chamar de Rafael"
    )

    assert name == "Rafael"


def test_returns_none_when_name_is_not_present():
    service = LeadIdentificationService()

    name = service.extract_name(
        "Quero um apartamento no Boa Vista"
    )

    assert name is None