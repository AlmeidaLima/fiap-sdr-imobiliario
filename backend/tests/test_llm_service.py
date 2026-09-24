import json

from app.schemas.conversation import (
    ConversationQualification,
    ConversationState,
)
from app.services.llm_client import LLMClientError
from app.services.llm_service import LLMService


class FakeLLMClient:

    def __init__(self):
        self.messages = None

    def chat(
            self,
            messages: list[dict[str, str]],
    ) -> str:
        self.messages = messages

        return "Resposta gerada pelo LLM"


def create_context():
    return {
        "conversation_state": ConversationState(
            conversation_id="llm-service-001",
            neighborhood="Boa Vista",
            max_price=700000,
            min_bedrooms=3,
        ),
        "qualification": ConversationQualification(
            qualified=True,
            missing_fields=[],
            next_question=None,
        ),
    }


def test_generate_response_uses_llm_client():
    client = FakeLLMClient()

    service = LLMService(
        client=client,
    )

    response = service.generate_response(
        user_message="Procuro um apartamento no Boa Vista.",
        **create_context(),
    )

    assert response == "Resposta gerada pelo LLM"

    assert client.messages is not None
    context = json.loads(
        client.messages[-1]["content"].split("\n\n", 1)[1]
    )

    assert context["mensagem_atual"] == (
        "Procuro um apartamento no Boa Vista."
    )
    assert context["estado_factual"]["neighborhood"] == "Boa Vista"

def test_generate_response_sends_system_prompt():
    client = FakeLLMClient()

    service = LLMService(
        client=client,
    )

    service.generate_response(
        user_message="Quero comprar um imóvel.",
        **create_context(),
    )

    assert client.messages is not None

    assert client.messages[0] == {
        "role": "system",
        "content": LLMService.SYSTEM_PROMPT,
    }

    assert "não invente" in LLMService.SYSTEM_PROMPT.lower()
    assert "imoveis_recuperados" in LLMService.SYSTEM_PROMPT


def test_generate_response_sends_controlled_property_context():
    client = FakeLLMClient()
    service = LLMService(client=client)

    service.generate_response(
        user_message="Quais opções você encontrou?",
        conversation_history=[
            {"role": "user", "content": f"mensagem {index}"}
            for index in range(8)
        ],
        properties_context=[
            {
                "id": 10,
                "external_id": "property-10",
                "price": "650000.00",
                "bedrooms": 3,
            }
        ],
        **create_context(),
    )

    assert client.messages is not None
    assert len(client.messages[1:-1]) == 6
    assert client.messages[1]["content"] == "mensagem 2"

    context = json.loads(
        client.messages[-1]["content"].split("\n\n", 1)[1]
    )

    assert context["imoveis_recuperados"] == [
        {
            "id": 10,
            "external_id": "property-10",
            "price": "650000.00",
            "bedrooms": 3,
        }
    ]


def test_generate_response_includes_deterministic_next_question():
    client = FakeLLMClient()
    service = LLMService(client=client)
    question = "Qual é o seu orçamento máximo?"

    service.generate_response(
        user_message="Quero um apartamento.",
        conversation_state=ConversationState(
            conversation_id="llm-service-002",
        ),
        qualification=ConversationQualification(
            qualified=False,
            missing_fields=["max_price"],
            next_question=question,
        ),
    )

    context = json.loads(
        client.messages[-1]["content"].split("\n\n", 1)[1]
    )

    assert context["qualificacao"]["next_question"] == question
    assert context["imoveis_recuperados"] == []

def test_generate_response_propagates_llm_client_error():
    class FailingLLMClient:

        def chat(
                self,
                messages: list[dict[str, str]],
        ) -> str:
            raise LLMClientError(
                "Erro ao comunicar com o LLM."
            )

    service = LLMService(
        client=FailingLLMClient(),
    )

    try:
        service.generate_response(
            user_message="Quero um apartamento.",
            **create_context(),
        )

    except LLMClientError as exc:
        assert str(exc) == (
            "Erro ao comunicar com o LLM."
        )

    else:
        raise AssertionError(
            "LLMClientError deveria ter sido propagado."
        )
