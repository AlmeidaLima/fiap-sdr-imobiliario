from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.message import Message


class MessageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            conversation_id: int,
            role: str,
            content: str,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    def create_without_commit(
            self,
            conversation_id: int,
            role: str,
            content: str,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.db.add(message)
        self.db.flush()
        self.db.refresh(message)
        return message

    def find_by_conversation_id(
            self,
            conversation_id: int,
    ) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.created_at.asc(),
                Message.id.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def list_public_messages(
            self,
            conversation_id: int,
            after_id: int | None = None,
    ) -> list[Message]:
        statement = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.role.in_(("user", "assistant")),
        )
        if after_id is not None:
            statement = statement.where(Message.id > after_id)
        statement = statement.order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
        return list(self.db.scalars(statement).all())
