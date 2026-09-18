from uuid import uuid4

from fastapi.testclient import TestClient

from app.database.conversation_repository import (
    ConversationRepository,
)
from app.database.lead_repository import (
    LeadRepository,
)
from app.database.message_repository import (
    MessageRepository,
)
from app.database.session import SessionLocal
from app.main import app


client = TestClient(app)


def test_conversation_preserves_state_without_client_state():
    conversation_id = f"test-{uuid4()}"

    first_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Quero um apartamento no Boa Vista",
        },
    )

    assert first_response.status_code == 200

    first_body = first_response.json()

    assert (
            first_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            first_body["qualification"]["qualified"]
            is False
    )

    second_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Até 700 mil",
        },
    )

    assert second_response.status_code == 200

    second_body = second_response.json()

    assert (
            second_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            second_body["state"]["max_price"]
            == "700000"
    )

    assert (
            second_body["qualification"]["qualified"]
            is False
    )

    third_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Preciso de 3 quartos",
        },
    )

    assert third_response.status_code == 200

    third_body = third_response.json()

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

    assert (
            third_body["qualification"]["qualified"]
            is True
    )


def test_conversation_recovers_persisted_state():
    conversation_id = f"test-{uuid4()}"

    first_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Quero um apartamento no Boa Vista",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Até 700 mil",
        },
    )

    assert second_response.status_code == 200

    third_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Quero também 2 banheiros",
        },
    )

    assert third_response.status_code == 200

    body = third_response.json()

    assert (
            body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            body["state"]["max_price"]
            == "700000"
    )

    assert (
            body["state"]["min_bathrooms"]
            == 2
    )

    assert (
            "Quero um apartamento no Boa Vista"
            in body["state"]["semantic_preferences"]
    )

    assert (
            "Até 700 mil"
            in body["state"]["semantic_preferences"]
    )

    assert (
            "Quero também 2 banheiros"
            in body["state"]["semantic_preferences"]
    )


def test_conversation_creates_and_associates_lead():
    conversation_id = f"test-{uuid4()}"

    response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Meu nome é Rafael Almeida",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
            body["conversation_id"]
            == conversation_id
    )

    assert (
            body["state"]["lead_name"]
            == "Rafael Almeida"
    )

    db = SessionLocal()

    try:
        conversation_repository = (
            ConversationRepository(db)
        )

        lead_repository = LeadRepository(db)

        conversation = (
            conversation_repository
            .find_by_conversation_id(
                conversation_id
            )
        )

        assert conversation is not None
        assert conversation.lead_id is not None

        lead = lead_repository.find_by_id(
            conversation.lead_id
        )

        assert lead is not None

        assert (
                lead.name
                == "Rafael Almeida"
        )

    finally:
        db.close()


def test_conversation_preserves_lead_across_multiple_turns():
    conversation_id = f"test-{uuid4()}"

    # Turno 1 - cliente informa o nome
    first_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Meu nome é Rafael Almeida",
        },
    )

    assert first_response.status_code == 200

    first_body = first_response.json()

    assert (
            first_body["state"]["lead_name"]
            == "Rafael Almeida"
    )

    # Recupera a conversa após o primeiro turno
    db = SessionLocal()

    try:
        conversation_repository = (
            ConversationRepository(db)
        )

        lead_repository = LeadRepository(db)

        conversation = (
            conversation_repository
            .find_by_conversation_id(
                conversation_id
            )
        )

        assert conversation is not None
        assert conversation.lead_id is not None

        original_lead_id = conversation.lead_id

        lead = lead_repository.find_by_id(
            original_lead_id
        )

        assert lead is not None
        assert lead.name == "Rafael Almeida"

    finally:
        db.close()

    # Turno 2 - informa o bairro
    second_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": (
                "Quero um apartamento no Boa Vista"
            ),
        },
    )

    assert second_response.status_code == 200

    second_body = second_response.json()

    assert (
            second_body["state"]["lead_name"]
            == "Rafael Almeida"
    )

    assert (
            second_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    # Turno 3 - informa o orçamento
    third_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Até 700 mil",
        },
    )

    assert third_response.status_code == 200

    third_body = third_response.json()

    assert (
            third_body["state"]["lead_name"]
            == "Rafael Almeida"
    )

    assert (
            third_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            third_body["state"]["max_price"]
            == "700000"
    )

    # Turno 4 - informa quantidade de quartos
    fourth_response = client.post(
        "/api/v1/conversations/turn",
        json={
            "conversation_id": conversation_id,
            "message": "Preciso de 3 quartos",
        },
    )

    assert fourth_response.status_code == 200

    fourth_body = fourth_response.json()

    assert (
            fourth_body["state"]["lead_name"]
            == "Rafael Almeida"
    )

    assert (
            fourth_body["state"]["neighborhood"]
            == "Boa Vista"
    )

    assert (
            fourth_body["state"]["max_price"]
            == "700000"
    )

    assert (
            fourth_body["state"]["min_bedrooms"]
            == 3
    )

    assert (
            fourth_body["qualification"]["qualified"]
            is True
    )

    # Validação final diretamente no PostgreSQL
    db = SessionLocal()

    try:
        conversation_repository = (
            ConversationRepository(db)
        )

        lead_repository = LeadRepository(db)

        conversation = (
            conversation_repository
            .find_by_conversation_id(
                conversation_id
            )
        )

        assert conversation is not None

        # A conversa deve continuar associada
        # exatamente ao mesmo Lead.
        assert (
                conversation.lead_id
                == original_lead_id
        )

        lead = lead_repository.find_by_id(
            conversation.lead_id
        )

        assert lead is not None

        assert (
                lead.name
                == "Rafael Almeida"
        )

        # O estado acumulado também deve
        # estar persistido no PostgreSQL.
        assert (
                conversation.state["lead_name"]
                == "Rafael Almeida"
        )

        assert (
                conversation.state["neighborhood"]
                == "Boa Vista"
        )

        assert (
                conversation.state["max_price"]
                == "700000"
        )

        assert (
                conversation.state["min_bedrooms"]
                == 3
        )

    finally:
        db.close()


def test_conversation_persists_message_history():
    conversation_id = f"test-{uuid4()}"

    messages = [
        "Meu nome é Rafael Almeida",
        "Quero um apartamento no Boa Vista",
        "Até 700 mil",
        "Preciso de 3 quartos",
    ]

    for message in messages:
        response = client.post(
            "/api/v1/conversations/turn",
            json={
                "conversation_id": conversation_id,
                "message": message,
            },
        )

        assert response.status_code == 200

    db = SessionLocal()

    try:
        conversation_repository = (
            ConversationRepository(db)
        )

        message_repository = MessageRepository(db)

        conversation = (
            conversation_repository
            .find_by_conversation_id(
                conversation_id
            )
        )

        assert conversation is not None

        persisted_messages = (
            message_repository
            .find_by_conversation_id(
                conversation.id
            )
        )

        assert len(persisted_messages) == 4

        assert [
                   message.role
                   for message in persisted_messages
               ] == [
                   "user",
                   "user",
                   "user",
                   "user",
               ]

        assert [
                   message.content
                   for message in persisted_messages
               ] == messages

    finally:
        db.close()