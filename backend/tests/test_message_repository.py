from uuid import uuid4

from app.database.conversation_repository import ConversationRepository
from app.database.message_repository import MessageRepository
from app.database.session import SessionLocal


def test_create_message():
    db = SessionLocal()

    try:
        conversation_repository = ConversationRepository(db)
        message_repository = MessageRepository(db)

        conversation = conversation_repository.create(
            conversation_id=f"test-{uuid4()}",
        )

        message = message_repository.create(
            conversation_id=conversation.id,
            role="user",
            content="Quero um apartamento no Boa Vista",
        )

        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == "user"
        assert message.content == "Quero um apartamento no Boa Vista"
        assert message.created_at is not None

    finally:
        db.close()


def test_find_messages_by_conversation_id():
    db = SessionLocal()

    try:
        conversation_repository = ConversationRepository(db)
        message_repository = MessageRepository(db)

        conversation = conversation_repository.create(
            conversation_id=f"test-{uuid4()}",
        )

        message_repository.create(
            conversation_id=conversation.id,
            role="user",
            content="Quero um apartamento no Boa Vista",
        )

        message_repository.create(
            conversation_id=conversation.id,
            role="assistant",
            content="Qual é o valor máximo que você pretende investir?",
        )

        messages = message_repository.find_by_conversation_id(
            conversation.id
        )

        assert len(messages) == 2

        assert messages[0].role == "user"
        assert messages[0].content == (
            "Quero um apartamento no Boa Vista"
        )

        assert messages[1].role == "assistant"
        assert messages[1].content == (
            "Qual é o valor máximo que você pretende investir?"
        )

    finally:
        db.close()