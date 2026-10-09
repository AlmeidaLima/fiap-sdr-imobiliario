from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.database.conversation_repository import ranked_conversations_subquery


@dataclass(frozen=True)
class DashboardLeadRecord:
    lead: Lead
    conversation: Conversation
    last_interaction_at: datetime | None


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_leads(self) -> list[DashboardLeadRecord]:
        ranked = ranked_conversations_subquery()
        statement = (
            select(
                Lead,
                Conversation,
                ranked.c.last_interaction_at,
            )
            .join(Conversation, Conversation.lead_id == Lead.id)
            .join(ranked, ranked.c.conversation_pk == Conversation.id)
            .where(ranked.c.conversation_rank == 1)
            .order_by(
                ranked.c.last_interaction_at.desc().nulls_last(),
                Lead.id.desc(),
            )
        )

        return [
            DashboardLeadRecord(
                lead=row[0],
                conversation=row[1],
                last_interaction_at=row[2],
            )
            for row in self.db.execute(statement).all()
        ]

    def get_lead(self, lead_id: int) -> Lead | None:
        return self.db.get(Lead, lead_id)

    def get_lead_record(self, lead_id: int) -> DashboardLeadRecord | None:
        ranked = ranked_conversations_subquery()
        statement = (
            select(
                Lead,
                Conversation,
                ranked.c.last_interaction_at,
            )
            .join(Conversation, Conversation.lead_id == Lead.id)
            .join(ranked, ranked.c.conversation_pk == Conversation.id)
            .where(
                Lead.id == lead_id,
                ranked.c.conversation_rank == 1,
            )
        )
        row = self.db.execute(statement).one_or_none()
        if row is None:
            return None

        return DashboardLeadRecord(
            lead=row[0],
            conversation=row[1],
            last_interaction_at=row[2],
        )

    def list_public_messages(self, conversation_id: int) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role.in_(("user", "assistant")),
            )
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list(self.db.scalars(statement).all())
