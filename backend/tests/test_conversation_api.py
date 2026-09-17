from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_conversation_first_turn_returns_next_question():
    response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": "api-conversation-001",
            "message": (
                "Quero um apartamento no Boa Vista"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
            body["conversation_id"]
            == "api-conversation-001"
    )

    assert (
            body["state"]["conversation_id"]
            == "api-conversation-001"
    )

    assert (
            body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert body["state"]["max_price"] is None
    assert body["state"]["min_bedrooms"] is None

    assert (
            body["qualification"]["qualified"]
            is False
    )

    assert (
            body["qualification"]["missing_fields"]
            == [
                "max_price",
                "min_bedrooms",
            ]
    )

    assert (
            body["qualification"]["next_question"]
            == (
                "Qual é o valor máximo que você "
                "pretende investir no imóvel?"
            )
    )

    assert body["properties"] == []


def test_conversation_api_preserves_state_between_turns():
    # ============================================================
    # TURNO 1
    # Cliente informa o bairro.
    # ============================================================

    first_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": "api-conversation-002",
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
            first_body["qualification"]["missing_fields"]
            == [
                "max_price",
                "min_bedrooms",
            ]
    )

    assert first_body["properties"] == []

    # ============================================================
    # TURNO 2
    # Cliente informa o orçamento.
    # O bairro deve continuar no estado da conversa.
    # ============================================================

    second_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": "api-conversation-002",
            "message": "Até 700 mil",
            "state": state,
        },
    )

    assert second_response.status_code == 200

    second_body = second_response.json()

    assert (
            second_body["conversation_id"]
            == "api-conversation-002"
    )

    assert (
            second_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            second_body["state"]["max_price"]
            == "700000"
    )

    assert (
            second_body["state"]["min_bedrooms"]
            is None
    )

    assert (
            second_body["qualification"]["qualified"]
            is False
    )

    assert (
            second_body["qualification"]["missing_fields"]
            == ["min_bedrooms"]
    )

    assert (
            second_body["qualification"]["next_question"]
            == "Quantos quartos você procura?"
    )

    assert second_body["properties"] == []

    # ============================================================
    # TURNO 3
    # Cliente informa a quantidade de quartos.
    # Agora a conversa deve ficar qualificada e executar a busca.
    # ============================================================

    state = second_body["state"]

    third_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": "api-conversation-002",
            "message": (
                "Quero pelo menos 3 quartos"
            ),
            "state": state,
        },
    )

    assert third_response.status_code == 200

    third_body = third_response.json()

    assert (
            third_body["conversation_id"]
            == "api-conversation-002"
    )

    # ============================================================
    # VALIDA ESTADO ACUMULADO
    # ============================================================

    assert (
            third_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            third_body["state"]["max_price"]
            == "700000"
    )

    assert (
            third_body["state"]["min_bedrooms"]
            == 3
    )

    # ============================================================
    # VALIDA QUALIFICAÇÃO
    # ============================================================

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

    # ============================================================
    # VALIDA CONTRATO DOS RESULTADOS
    # ============================================================

    assert isinstance(
        third_body["properties"],
        list,
    )

    # ============================================================
    # VALIDA RESULTADOS REAIS DA BUSCA
    #
    # A conversa acumulou:
    # - bairro: Boa Vista
    # - preço máximo: 700000
    # - mínimo de quartos: 3
    #
    # Os imóveis encontrados pela busca híbrida devem respeitar
    # esses filtros.
    # ============================================================

    properties = third_body["properties"]

    assert len(properties) > 0
    assert len(properties) <= 5

    for property_data in properties:
        assert (
                property_data["neighborhood"]
                == "Boa Vista"
        )

        assert (
                float(property_data["price"])
                <= 700000
        )

        assert (
                property_data["bedrooms"]
                >= 3
        )

        assert (
                property_data["similarity_score"]
                is not None
        )