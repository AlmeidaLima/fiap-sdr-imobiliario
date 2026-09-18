from app.database.conversation_repository import ConversationRepository
from app.database.lead_repository import LeadRepository
from app.database.message_repository import MessageRepository
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message


class ConversationPersistenceService:

    def __init__(
            self,
            conversation_repository: ConversationRepository,
            message_repository: MessageRepository,
            lead_repository: LeadRepository | None = None,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.lead_repository = lead_repository

    def get_or_create(
            self,
            conversation_id: str,
    ) -> Conversation:
        conversation = (
            self.conversation_repository.find_by_conversation_id(
                conversation_id
            )
        )

        if conversation is not None:
            return conversation

        return self.conversation_repository.create(
            conversation_id=conversation_id,
            state={},
        )

    def update_state(
            self,
            conversation: Conversation,
            state: dict,
    ) -> Conversation:
        return self.conversation_repository.update_state(
            conversation=conversation,
            state=state,
        )

    def save_message(
            self,
            conversation: Conversation,
            role: str,
            content: str,
    ) -> Message:
        return self.message_repository.create(
            conversation_id=conversation.id,
            role=role,
            content=content,
        )

    def get_messages(
            self,
            conversation: Conversation,
    ) -> list[Message]:
        return self.message_repository.find_by_conversation_id(
            conversation.id
        )

    def create_and_associate_lead(
            self,
            conversation: Conversation,
            name: str,
    ) -> Lead:
        if self.lead_repository is None:
            raise ValueError(
                "LeadRepository is required to create a lead."
            )

        if conversation.lead_id is not None:
            lead = self.lead_repository.find_by_id(
                conversation.lead_id
            )

            if lead is not None:
                return lead

        lead = self.lead_repository.create(
            name=name,
        )

        self.conversation_repository.associate_lead(
            conversation=conversation,
            lead_id=lead.id,
        )

        return lead