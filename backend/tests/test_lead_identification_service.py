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

def test_extracts_name_before_conversational_continuation():
    service = LeadIdentificationService()

    name = service.extract_name(
        "Olá, meu nome é Rafael e estou procurando "
        "um apartamento para comprar."
    )

    assert name == "Rafael"


def test_extracts_compound_name_before_conversational_continuation():
    service = LeadIdentificationService()

    name = service.extract_name(
        "Meu nome é Rafael Almeida e estou procurando um apartamento."
    )

    assert name == "Rafael Almeida"


def test_extracts_name_before_other_explicit_continuations():
    service = LeadIdentificationService()

    messages = [
        "Meu nome é Rafael e quero comprar um apartamento.",
        "Meu nome é Rafael e procuro um imóvel.",
        "Meu nome é Rafael e preciso de um apartamento.",
    ]

    for message in messages:
        assert service.extract_name(message) == "Rafael"
