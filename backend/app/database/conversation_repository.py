from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lead import Lead  # noqa: F401
from app.models.conversation import Conversation
from app.models.message import Message


def ranked_conversations_subquery():
    last_interaction = (
        select(
            Message.conversation_id.label("conversation_pk"),
            func.max(Message.created_at).label("last_interaction_at"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    return (
        select(
            Conversation.id.label("conversation_pk"),
            last_interaction.c.last_interaction_at,
            func.row_number().over(
                partition_by=Conversation.lead_id,
                order_by=(
                    last_interaction.c.last_interaction_at.desc().nulls_last(),
                    Conversation.updated_at.desc(),
                    Conversation.id.desc(),
                ),
            ).label("conversation_rank"),
        )
        .outerjoin(
            last_interaction,
            last_interaction.c.conversation_pk == Conversation.id,
        )
        .where(Conversation.lead_id.is_not(None))
        .subquery()
    )


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

    def find_latest_by_lead_id(self, lead_id: int) -> Conversation | None:
        ranked = ranked_conversations_subquery()
        statement = (
            select(Conversation)
            .join(ranked, ranked.c.conversation_pk == Conversation.id)
            .where(
                Conversation.lead_id == lead_id,
                ranked.c.conversation_rank == 1,
            )
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
