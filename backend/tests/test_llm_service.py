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

    instruction, serialized_context = (
        client.messages[-1]["content"].split("\n\n", 1)
    )
    context = json.loads(serialized_context)

    assert context["qualificacao"]["next_question"] == question
    assert context["situacao_busca"] == "NAO_EXECUTADA"
    assert context["imoveis_recuperados"] == []
    assert "busca de imóveis ainda não foi executada" in instruction.lower()
    assert "próxima pergunta" in instruction.lower()
    assert "nunca diga que não encontrou imóveis" in instruction.lower()


def test_generate_response_marks_search_without_results():
    client = FakeLLMClient()
    service = LLMService(client=client)

    service.generate_response(
        user_message="Quais opções você encontrou?",
        properties_context=[],
        **create_context(),
    )

    instruction, serialized_context = (
        client.messages[-1]["content"].split("\n\n", 1)
    )
    context = json.loads(serialized_context)

    assert context["situacao_busca"] == "EXECUTADA_SEM_RESULTADOS"
    assert context["imoveis_recuperados"] == []
    assert "busca de imóveis foi executada" in instruction.lower()
    assert "ausência de resultados" in instruction.lower()
    assert "sem inventar imóveis" in instruction.lower()


def test_generate_response_marks_search_with_results():
    client = FakeLLMClient()
    service = LLMService(client=client)
    property_context = {
        "id": 10,
        "price": "650000.00",
        "bedrooms": 3,
    }

    service.generate_response(
        user_message="Quais opções você encontrou?",
        properties_context=[property_context],
        **create_context(),
    )

    instruction, serialized_context = (
        client.messages[-1]["content"].split("\n\n", 1)
    )
    context = json.loads(serialized_context)

    assert context["situacao_busca"] == "EXECUTADA_COM_RESULTADOS"
    assert context["imoveis_recuperados"] == [property_context]
    assert "busca de imóveis foi executada" in instruction.lower()
    assert "somente os imóveis presentes" in instruction.lower()
    assert "sem inventar imóveis, preços ou atributos" in instruction.lower()

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
