from uuid import uuid4

from app.database.conversation_repository import ConversationRepository
from app.database.message_repository import MessageRepository
from app.database.session import SessionLocal
from app.models.message import Message


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


def test_create_without_commit_can_be_rolled_back():
    db = SessionLocal()
    try:
        conversation = ConversationRepository(db).create(
            conversation_id=f"test-{uuid4()}",
        )
        repository = MessageRepository(db)
        message = repository.create_without_commit(
            conversation_id=conversation.id,
            role="assistant",
            content="Mensagem transacional",
        )
        message_id = message.id
        db.rollback()
        assert db.get(Message, message_id) is None
    finally:
        db.close()


def test_public_messages_filter_roles_order_and_after_id():
    db = SessionLocal()
    try:
        conversation = ConversationRepository(db).create(
            conversation_id=f"test-{uuid4()}",
        )
        repository = MessageRepository(db)
        first = repository.create(conversation.id, "user", "Primeira")
        repository.create(conversation.id, "system", "Interna")
        second = repository.create(conversation.id, "assistant", "Segunda")

        messages = repository.list_public_messages(conversation.id)
        incremental = repository.list_public_messages(
            conversation.id,
            after_id=first.id,
        )

        assert [item.id for item in messages] == [first.id, second.id]
        assert [item.id for item in incremental] == [second.id]
    finally:
        db.close()
