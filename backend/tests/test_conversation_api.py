import io
import logging
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.conversation_repository import ConversationRepository
from app.database.message_repository import MessageRepository
from app.database.session import SessionLocal
from app.core.observability import SafeKeyValueFormatter


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_client.LLMClient.chat",
        lambda self, messages: "Resposta natural do assistente.",
    )


def test_conversation_first_turn_returns_next_question():
    conversation_id = f"test-{uuid4()}"

    response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": (
                "Quero um apartamento no Boa Vista"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
            body["conversation_id"]
            == conversation_id
    )

    assert (
            body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            body["qualification"]["qualified"]
            is False
    )

    assert (
            "max_price"
            in body["qualification"]["missing_fields"]
    )

    assert (
            "min_bedrooms"
            in body["qualification"]["missing_fields"]
    )

    assert (
            body["qualification"]["next_question"]
            is not None
    )

    assert body["properties"] == []
    assert isinstance(body["user_message_id"], int)
    assert isinstance(body["assistant_message_id"], int)
    assert body["assistant_message_id"] > body["user_message_id"]
    assert body["user_message_created_at"]
    assert body["assistant_message_created_at"]


def test_get_public_conversation_messages_and_after_id():
    conversation_id = f"test-{uuid4()}"
    turn = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Quero comprar um apartamento",
        },
    )
    assert turn.status_code == 200
    body = turn.json()

    db = SessionLocal()
    try:
        conversation = ConversationRepository(db).find_by_conversation_id(
            conversation_id
        )
        MessageRepository(db).create(
            conversation_id=conversation.id,
            role="system",
            content="Mensagem interna",
        )
    finally:
        db.close()

    history = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )
    assert history.status_code == 200
    assert [item["role"] for item in history.json()["messages"]] == [
        "user", "assistant",
    ]
    assert [item["id"] for item in history.json()["messages"]] == [
        body["user_message_id"],
        body["assistant_message_id"],
    ]
    assert history.json()["state"]["commercial_intent"] == "COMPRA"
    assert history.json()["state"]["lead_score"] == 20
    assert history.json()["state"]["lead_classification"] == "FRIO"
    assert history.json()["qualification"]["qualified"] is False

    incremental = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={"after_id": body["user_message_id"]},
    )
    assert incremental.status_code == 200
    assert [item["id"] for item in incremental.json()["messages"]] == [
        body["assistant_message_id"],
    ]


def test_get_messages_returns_empty_and_validates_after_id():
    conversation_id = f"test-empty-{uuid4()}"
    db = SessionLocal()
    try:
        ConversationRepository(db).create(conversation_id=conversation_id)
    finally:
        db.close()

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["messages"] == []
    assert body["state"]["conversation_id"] == conversation_id
    assert body["state"]["lead_score"] == 0
    assert body["qualification"]["qualified"] is False

    invalid = client.get(
        f"/api/v1/conversations/{conversation_id}/messages?after_id=-1"
    )
    assert invalid.status_code == 422


def test_get_messages_returns_conversation_not_found():
    response = client.get(
        f"/api/v1/conversations/missing-{uuid4()}/messages"
    )
    assert response.status_code == 404
    assert response.json()["error"] == "conversation_not_found"


def test_conversation_api_preserves_state_between_turns():
    conversation_id = f"test-{uuid4()}"

    # ============================================================
    # TURNO 1
    # Cliente informa o bairro.
    # ============================================================

    first_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": (
                "Quero um apartamento no Boa Vista"
            ),
        },
    )

    assert first_response.status_code == 200

    first_body = first_response.json()

    state = first_body["state"]

    assert (
            state["neighborhood"]
            == "Boa Vista"
    )

    assert (
            first_body["qualification"]["qualified"]
            is False
    )

    assert (
            "max_price"
            in first_body["qualification"]["missing_fields"]
    )

    assert (
            "min_bedrooms"
            in first_body["qualification"]["missing_fields"]
    )

    # ============================================================
    # TURNO 2
    # Cliente informa o orçamento.
    #
    # O state continua sendo enviado para manter compatibilidade
    # com o teste criado na Missão 08.
    #
    # A partir da Missão 09, a API também recupera o estado
    # persistido pelo conversation_id.
    # ============================================================

    second_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Até 700 mil",
            "state": state,
        },
    )

    assert second_response.status_code == 200

    second_body = second_response.json()

    state = second_body["state"]

    assert (
            state["neighborhood"]
            == "Boa Vista"
    )

    assert (
            state["max_price"]
            == "700000"
    )

    assert (
            second_body["qualification"]["qualified"]
            is False
    )

    assert (
            "min_bedrooms"
            in second_body["qualification"]["missing_fields"]
    )

    # ============================================================
    # TURNO 3
    # Cliente informa a quantidade de quartos.
    # ============================================================

    third_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Preciso de 3 quartos",
            "state": state,
        },
    )

    assert third_response.status_code == 200

    third_body = third_response.json()

    final_state = third_body["state"]

    assert (
            third_body["conversation_id"]
            == conversation_id
    )

    assert (
            final_state["neighborhood"]
            == "Boa Vista"
    )

    assert (
            final_state["max_price"]
            == "700000"
    )

    assert (
            final_state["min_bedrooms"]
            == 3
    )

    assert (
            third_body["qualification"]["qualified"]
            is True
    )

    assert (
            third_body["qualification"]["missing_fields"]
            == []
    )

    assert (
            third_body["qualification"]["next_question"]
            is None
    )


def test_unqualified_turn_does_not_initialize_embedding_service(
        monkeypatch,
):
    conversation_id = f"test-{uuid4()}"

    def fail_if_initialized():
        raise AssertionError(
            "EmbeddingService não deve ser inicializado "
            "em um turno ainda não qualificado."
        )

    monkeypatch.setattr(
        "app.api.routes.conversations.EmbeddingService",
        fail_if_initialized,
    )

    response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": (
                "Quero um apartamento no Boa Vista"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["qualification"]["qualified"] is False

    assert (
            body["qualification"]["next_question"]
            is not None
    )

    assert body["properties"] == []
    assert body["response"] == "Resposta natural do assistente."


def test_conversation_uses_fallback_when_llm_is_unavailable(
        monkeypatch,
):
    from app.services.llm_client import LLMClientError

    def fail_chat(self, messages):
        raise LLMClientError("LLM indisponível")

    monkeypatch.setattr(
        "app.services.llm_client.LLMClient.chat",
        fail_chat,
    )

    response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": f"test-{uuid4()}",
            "message": "Quero um apartamento no Boa Vista",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == body["qualification"]["next_question"]


def test_conversation_limits_llm_history_to_six_records(monkeypatch):
    captured_messages = []

    def capture_chat(self, messages):
        captured_messages.append(messages)
        return "Resposta natural do assistente."

    monkeypatch.setattr(
        "app.services.llm_client.LLMClient.chat",
        capture_chat,
    )
    conversation_id = f"test-{uuid4()}"

    for index in range(5):
        response = client.post(
            "/api/v1/conversations/turn",
            json={
                "conversation_id": conversation_id,
                "message": f"Ainda estou pesquisando imóveis {index}",
            },
        )
        assert response.status_code == 200

    last_request = captured_messages[-1]
    history = last_request[1:-1]

    assert len(history) == 6
    assert [message["role"] for message in history] == [
        "user", "assistant", "user", "assistant", "user", "assistant",
    ]


def test_conversation_turn_logs_safe_events_with_request_id():
    logger = logging.getLogger("app")
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(SafeKeyValueFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    conversation_id = f"observability-{uuid4()}"
    request_id = "ea22ec31-9ff2-43cd-8ea4-e115754ee508"

    try:
        response = client.post(
            "/api/v1/conversations/turn",
            headers={"X-Request-ID": request_id},
            json={
                "conversation_id": conversation_id,
                "message": "SEGREDO_TESTE_CONVERSA",
            },
        )
    finally:
        logger.handlers = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate

    assert response.status_code == 200
    assert "event=conversation_turn_started" in output.getvalue()
    assert "event=conversation_turn_completed" in output.getvalue()
    assert f"request_id={request_id}" in output.getvalue()
    assert f"conversation_id={conversation_id}" in output.getvalue()
    assert "qualified=false" in output.getvalue()
    assert "property_count=0" in output.getvalue()
    assert "SEGREDO_TESTE_CONVERSA" not in output.getvalue()
