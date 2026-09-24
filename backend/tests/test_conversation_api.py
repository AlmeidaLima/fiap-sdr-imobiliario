from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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