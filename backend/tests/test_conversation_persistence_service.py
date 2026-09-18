from uuid import uuid4

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
from app.services.conversation_persistence_service import (
    ConversationPersistenceService,
)


def create_service(
        db,
        with_lead_repository: bool = False,
):
    lead_repository = None

    if with_lead_repository:
        lead_repository = LeadRepository(db)

    return ConversationPersistenceService(
        conversation_repository=ConversationRepository(db),
        message_repository=MessageRepository(db),
        lead_repository=lead_repository,
    )


def test_get_or_create_conversation():
    db = SessionLocal()

    try:
        service = create_service(db)

        conversation_id = f"test-{uuid4()}"

        first = service.get_or_create(
            conversation_id
        )

        second = service.get_or_create(
            conversation_id
        )

        assert first.id is not None
        assert second.id == first.id
        assert second.conversation_id == conversation_id
        assert second.state == {}

    finally:
        db.close()


def test_persist_conversation_state():
    db = SessionLocal()

    try:
        service = create_service(db)

        conversation_id = f"test-{uuid4()}"

        conversation = service.get_or_create(
            conversation_id
        )

        service.update_state(
            conversation=conversation,
            state={
                "neighborhood": "Boa Vista",
                "max_price": "700000",
                "min_bedrooms": 3,
            },
        )

        recovered = service.get_or_create(
            conversation_id
        )

        assert (
                recovered.state["neighborhood"]
                == "Boa Vista"
        )

        assert (
                recovered.state["max_price"]
                == "700000"
        )

        assert (
                recovered.state["min_bedrooms"]
                == 3
        )

    finally:
        db.close()


def test_persist_conversation_messages():
    db = SessionLocal()

    try:
        service = create_service(db)

        conversation_id = f"test-{uuid4()}"

        conversation = service.get_or_create(
            conversation_id
        )

        service.save_message(
            conversation=conversation,
            role="user",
            content=(
                "Quero um apartamento no Boa Vista"
            ),
        )

        service.save_message(
            conversation=conversation,
            role="assistant",
            content=(
                "Qual é o valor máximo que "
                "você pretende investir?"
            ),
        )

        messages = service.get_messages(
            conversation
        )

        assert len(messages) == 2

        assert messages[0].role == "user"

        assert messages[0].content == (
            "Quero um apartamento no Boa Vista"
        )

        assert messages[1].role == "assistant"

        assert messages[1].content == (
            "Qual é o valor máximo que "
            "você pretende investir?"
        )

    finally:
        db.close()


def test_create_and_associate_lead():
    db = SessionLocal()

    try:
        service = create_service(
            db,
            with_lead_repository=True,
        )

        conversation_id = f"test-{uuid4()}"

        conversation = service.get_or_create(
            conversation_id
        )

        lead = service.create_and_associate_lead(
            conversation=conversation,
            name="Rafael Almeida",
        )

        recovered_conversation = (
            service.get_or_create(
                conversation_id
            )
        )

        assert lead.id is not None
        assert lead.name == "Rafael Almeida"

        assert (
                recovered_conversation.lead_id
                == lead.id
        )

    finally:
        db.close()


def test_does_not_create_second_lead_for_same_conversation():
    db = SessionLocal()

    try:
        service = create_service(
            db,
            with_lead_repository=True,
        )

        conversation_id = f"test-{uuid4()}"

        conversation = service.get_or_create(
            conversation_id
        )

        first_lead = (
            service.create_and_associate_lead(
                conversation=conversation,
                name="Rafael Almeida",
            )
        )

        second_lead = (
            service.create_and_associate_lead(
                conversation=conversation,
                name="Rafael Almeida",
            )
        )

        assert (
                first_lead.id
                == second_lead.id
        )

        assert (
                conversation.lead_id
                == first_lead.id
        )

    finally:
        db.close()