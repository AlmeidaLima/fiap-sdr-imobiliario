from typing import TypedDict

from app.schemas.conversation import (
    ConversationQualification,
    ConversationState,
)


class AgentState(TypedDict, total=False):
    conversation_id: str
    message: str
    limit: int

    conversation_state: ConversationState
    qualification: ConversationQualification

    conversation_history: list[dict[str, str]]
    properties: list

    response: str | None
    error: str | None
