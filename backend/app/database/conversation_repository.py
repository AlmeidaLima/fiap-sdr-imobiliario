from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead  # noqa: F401
from app.models.conversation import Conversation


class ConversationRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            conversation_id: str,
            state: dict | None = None,
            lead_id: int | None = None,
            status: str = "active",
    ) -> Conversation:
        conversation = Conversation(
            conversation_id=conversation_id,
            lead_id=lead_id,
            status=status,
            state=state or {},
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def find_by_conversation_id(
            self,
            conversation_id: str,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.conversation_id
            == conversation_id
        )

        return self.db.scalar(statement)

    def update_state(
            self,
            conversation: Conversation,
            state: dict,
    ) -> Conversation:
        conversation.state = state

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def associate_lead(
            self,
            conversation: Conversation,
            lead_id: int,
    ) -> Conversation:
        conversation.lead_id = lead_id

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation