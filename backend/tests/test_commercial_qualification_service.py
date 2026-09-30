import pytest

from app.services.commercial_qualification_service import (
    CommercialQualificationService,
)


@pytest.fixture
def service():
    return CommercialQualificationService()


@pytest.mark.parametrize(
    ("message", "expected_intent"),
    [
        ("Quero comprar um apartamento", "COMPRA"),
        ("Procuro apartamento para alugar", "ALUGUEL"),
        ("Quero um imóvel para investimento", "INVESTIMENTO"),
        ("Quero conhecer outras opções", "INDEFINIDO"),
    ],
)
def test_extracts_commercial_intent(service, message, expected_intent):
    result = service.extract(message)
    assert result.commercial_intent == expected_intent


@pytest.mark.parametrize(
    "message",
    [
        "Não quero comprar",
        "Não quero alugar",
        "Não quero investir",
        "Como funciona a compra?",
        "Como funciona o aluguel?",
    ],
)
def test_does_not_extract_negated_or_informational_intent(service, message):
    result = service.extract(message)
    assert result.commercial_intent == "INDEFINIDO"


@pytest.mark.parametrize(
    ("message", "expected_days"),
    [
        ("Preciso em 20 dias", 20),
        ("Quero comprar nos próximos 30 dias", 30),
        ("Daqui a 2 meses", 60),
        ("Em 3 meses", 90),
        ("Em 0 dias", None),
        ("Daqui a 0 meses", None),
        ("Em 1 dia", 1),
        ("Em 1 mês", 30),
        ("Ainda estou pesquisando", None),
    ],
)
def test_extracts_urgency_days(service, message, expected_days):
    result = service.extract(message)
    assert result.urgency_days == expected_days


@pytest.mark.parametrize(
    "message",
    [
        "Sim, podemos marcar uma visita",
        "Quero visitar o imóvel",
        "Podemos marcar uma reunião",
        "Quero marcar uma visita",
        "Podemos agendar uma visita",
        "Aceito uma visita",
    ],
)
def test_textual_interest_does_not_activate_commercial_acceptance(
        service,
        message,
):
    result = service.extract(message)
    assert result.accepted_meeting_or_visit is False


def test_question_about_visit_is_not_acceptance(service):
    result = service.extract("Como funciona a visita?")
    assert result.accepted_meeting_or_visit is False


@pytest.mark.parametrize(
    "message",
    [
        "Não quero visitar",
        "Não quero marcar uma reunião",
    ],
)
def test_does_not_extract_negated_acceptance(service, message):
    result = service.extract(message)
    assert result.accepted_meeting_or_visit is False


@pytest.mark.parametrize(
    ("message", "expected_intent"),
    [
        ("Estou procurando um apartamento para comprar.", "COMPRA"),
        ("Estou procurando um apartamento para alugar.", "ALUGUEL"),
        ("Estou procurando um imóvel para investir.", "INVESTIMENTO"),
        (
            "Olá, meu nome é Rafael e estou procurando "
            "um apartamento para comprar.",
            "COMPRA",
        ),
    ],
)
def test_extracts_commercial_intent_from_estou_procurando(
        service,
        message,
        expected_intent,
):
    result = service.extract(message)
    assert result.commercial_intent == expected_intent


@pytest.mark.parametrize(
    "message",
    [
        "Não estou procurando um apartamento para comprar.",
        "Procurando um apartamento para comprar.",
    ],
)
def test_estou_procurando_preserves_existing_intent_guardrails(
        service,
        message,
):
    result = service.extract(message)
    assert result.commercial_intent == "INDEFINIDO"

@pytest.mark.parametrize(
    ("message", "expected_days"),
    [
        ("Preciso do imóvel em até 30 dias.", 30),
        ("Quero comprar em até 2 meses.", 60),
        ("Preciso do imóvel em até 0 dias.", None),
    ],
)
def test_extracts_urgency_with_ate(
        service,
        message,
        expected_days,
):
    result = service.extract(message)

    assert result.urgency_days == expected_days
