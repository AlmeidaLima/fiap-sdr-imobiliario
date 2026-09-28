from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database.conversation_repository import ConversationRepository
from app.database.session import SessionLocal
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setattr(
        'app.services.llm_client.LLMClient.chat',
        lambda self, messages: 'Resposta natural do assistente.',
    )


def persist_state(conversation_id: str, state: dict) -> None:
    db = SessionLocal()
    try:
        ConversationRepository(db).create(
            conversation_id=conversation_id,
            state=state,
        )
    finally:
        db.close()


def recover_state(conversation_id: str) -> dict:
    db = SessionLocal()
    try:
        conversation = ConversationRepository(db).find_by_conversation_id(
            conversation_id,
        )
        return conversation.state
    finally:
        db.close()


def test_turn_without_selected_property_id_remains_compatible():
    conversation_id = f'selection-api-{uuid4()}'

    response = client.post(
        '/api/v1/conversations/turn',
        json={
            'conversation_id': conversation_id,
            'message': 'Quero um apartamento no Boa Vista',
        },
    )

    assert response.status_code == 200
    assert response.json()['state']['selected_property_id'] is None


def test_turn_selects_presented_property_and_persists_selection():
    conversation_id = f'selection-api-{uuid4()}'
    persist_state(
        conversation_id,
        {
            'presented_property_ids': [10, 20],
            'lead_score': 0,
            'accepted_meeting_or_visit': False,
        },
    )

    response = client.post(
        '/api/v1/conversations/turn',
        json={
            'conversation_id': conversation_id,
            'message': 'Tenho interesse neste imovel',
            'selected_property_id': 20,
        },
    )

    assert response.status_code == 200
    state = response.json()['state']
    assert state['presented_property_ids'] == [10, 20]
    assert state['selected_property_id'] == 20
    assert state['lead_score'] == 0
    assert state['accepted_meeting_or_visit'] is False
    assert recover_state(conversation_id)['selected_property_id'] == 20

    next_response = client.post(
        '/api/v1/conversations/turn',
        json={
            'conversation_id': conversation_id,
            'message': 'Meu nome e Rafael',
        },
    )

    assert next_response.status_code == 200
    next_state = next_response.json()['state']
    assert next_state['presented_property_ids'] == [10, 20]
    assert next_state['selected_property_id'] == 20


def test_turn_rejects_property_that_was_not_presented():
    conversation_id = f'selection-api-{uuid4()}'
    persist_state(
        conversation_id,
        {
            'presented_property_ids': [10],
            'selected_property_id': 10,
        },
    )

    response = client.post(
        '/api/v1/conversations/turn',
        json={
            'conversation_id': conversation_id,
            'message': 'Quero este imovel',
            'selected_property_id': 999,
        },
    )

    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_property_selection'
    assert recover_state(conversation_id)['selected_property_id'] == 10


def test_turn_does_not_trust_presented_properties_from_request_state():
    conversation_id = f'selection-api-{uuid4()}'
    persist_state(conversation_id, {})

    response = client.post(
        '/api/v1/conversations/turn',
        json={
            'conversation_id': conversation_id,
            'message': 'Quero este imovel',
            'selected_property_id': 999,
            'state': {
                'conversation_id': conversation_id,
                'presented_property_ids': [999],
            },
        },
    )

    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_property_selection'
