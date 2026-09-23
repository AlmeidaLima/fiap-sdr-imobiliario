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


def test_generate_response_uses_llm_client():
    client = FakeLLMClient()

    service = LLMService(
        client=client,
    )

    response = service.generate_response(
        user_message="Procuro um apartamento no Boa Vista.",
    )

    assert response == "Resposta gerada pelo LLM"

    assert client.messages is not None
    assert client.messages[-1] == {
        "role": "user",
        "content": "Procuro um apartamento no Boa Vista.",
    }

def test_generate_response_sends_system_prompt():
    client = FakeLLMClient()

    service = LLMService(
        client=client,
    )

    service.generate_response(
        user_message="Quero comprar um imóvel.",
    )

    assert client.messages is not None

    assert client.messages[0] == {
        "role": "system",
        "content": LLMService.SYSTEM_PROMPT,
    }

    assert "não invente informações sobre imóveis" in (
        LLMService.SYSTEM_PROMPT.lower()
    )

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
        )

    except LLMClientError as exc:
        assert str(exc) == (
            "Erro ao comunicar com o LLM."
        )

    else:
        raise AssertionError(
            "LLMClientError deveria ter sido propagado."
        )