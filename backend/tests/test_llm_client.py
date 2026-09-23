import httpx
import pytest

from app.services.llm_client import (
    LLMClient,
    LLMClientError,
)


def test_chat_returns_assistant_content(
        monkeypatch,
):
    def mock_post(*args, **kwargs):
        request = httpx.Request(
            "POST",
            "http://localhost:8080/v1/chat/completions",
        )

        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Olá! Como posso ajudar?",
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(
        httpx,
        "post",
        mock_post,
    )

    client = LLMClient(
        base_url="http://localhost:8080",
        model="local-model",
        timeout=30.0,
    )

    response = client.chat(
        messages=[
            {
                "role": "user",
                "content": "Olá",
            }
        ]
    )

    assert response == "Olá! Como posso ajudar?"


def test_chat_raises_error_on_timeout(
        monkeypatch,
):
    def mock_post(*args, **kwargs):
        raise httpx.TimeoutException(
            "LLM timeout",
        )

    monkeypatch.setattr(
        httpx,
        "post",
        mock_post,
    )

    client = LLMClient(
        base_url="http://localhost:8080",
        model="local-model",
        timeout=30.0,
    )

    with pytest.raises(
            LLMClientError,
            match="Timeout",
    ):
        client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Olá",
                }
            ]
        )


def test_chat_raises_error_on_http_error(
        monkeypatch,
):
    def mock_post(*args, **kwargs):
        request = httpx.Request(
            "POST",
            "http://localhost:8080/v1/chat/completions",
        )

        response = httpx.Response(
            500,
            request=request,
        )

        raise httpx.HTTPStatusError(
            "Internal Server Error",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        httpx,
        "post",
        mock_post,
    )

    client = LLMClient(
        base_url="http://localhost:8080",
        model="local-model",
        timeout=30.0,
    )

    with pytest.raises(
            LLMClientError,
            match="Erro ao comunicar com o LLM",
    ):
        client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Olá",
                }
            ]
        )


def test_chat_raises_error_on_connection_error(
        monkeypatch,
):
    def mock_post(*args, **kwargs):
        request = httpx.Request(
            "POST",
            "http://localhost:8080/v1/chat/completions",
        )

        raise httpx.ConnectError(
            "Connection refused",
            request=request,
        )

    monkeypatch.setattr(
        httpx,
        "post",
        mock_post,
    )

    client = LLMClient(
        base_url="http://localhost:8080",
        model="local-model",
        timeout=30.0,
    )

    with pytest.raises(
            LLMClientError,
            match="Erro ao comunicar com o LLM",
    ):
        client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Olá",
                }
            ]
        )


def test_chat_raises_error_on_invalid_response(
        monkeypatch,
):
    def mock_post(*args, **kwargs):
        request = httpx.Request(
            "POST",
            "http://localhost:8080/v1/chat/completions",
        )

        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [],
            },
        )

    monkeypatch.setattr(
        httpx,
        "post",
        mock_post,
    )

    client = LLMClient(
        base_url="http://localhost:8080",
        model="local-model",
        timeout=30.0,
    )

    with pytest.raises(
            LLMClientError,
            match="Resposta inválida",
    ):
        client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Olá",
                }
            ]
        )


def test_chat_sends_expected_request(
        monkeypatch,
):
    captured_request = {}

    def mock_post(
            url,
            json,
            timeout,
    ):
        captured_request["url"] = url
        captured_request["json"] = json
        captured_request["timeout"] = timeout

        request = httpx.Request(
            "POST",
            url,
        )

        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Resposta do LLM",
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(
        httpx,
        "post",
        mock_post,
    )

    client = LLMClient(
        base_url="http://localhost:8080/",
        model="local-model",
        timeout=30.0,
    )

    messages = [
        {
            "role": "system",
            "content": "Você é um SDR imobiliário.",
        },
        {
            "role": "user",
            "content": "Procuro um apartamento.",
        },
    ]

    client.chat(
        messages=messages,
    )

    assert captured_request["url"] == (
        "http://localhost:8080/v1/chat/completions"
    )

    assert captured_request["json"] == {
        "model": "local-model",
        "messages": messages,
    }

    assert captured_request["timeout"] == 30.0