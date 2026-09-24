from typing import Any

import httpx


class LLMClientError(Exception):
    """Erro ao comunicar com o servidor de LLM."""


class LLMClient:

    CHAT_COMPLETIONS_PATH = "/v1/chat/completions"

    def __init__(
            self,
            base_url: str,
            model: str,
            timeout: float,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(
            self,
            messages: list[dict[str, str]],
    ) -> str:
        url = (
            f"{self.base_url}"
            f"{self.CHAT_COMPLETIONS_PATH}"
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        try:
            response = httpx.post(
                url,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise LLMClientError(
                "Timeout ao comunicar com o LLM."
            ) from exc

        except httpx.HTTPError as exc:
            raise LLMClientError(
                "Erro ao comunicar com o LLM."
            ) from exc

        try:
            data = response.json()

            content = data["choices"][0]["message"]["content"]

        except (
                ValueError,
                KeyError,
                IndexError,
                TypeError,
        ) as exc:
            raise LLMClientError(
                "Resposta inválida retornada pelo LLM."
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMClientError(
                "Resposta inválida retornada pelo LLM."
            )

        return content