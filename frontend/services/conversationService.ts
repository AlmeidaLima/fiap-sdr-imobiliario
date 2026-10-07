import { apiClient } from "../lib/apiClient";
import type {
  ConversationTurnRequest,
  ConversationTurnResponse,
  ConversationMessagesResponse,
} from "../types/conversation";

const CONVERSATION_TURN_PATH = "/api/v1/conversations/turn";

export async function sendConversationTurn(
  request: ConversationTurnRequest,
): Promise<ConversationTurnResponse> {
  return apiClient<ConversationTurnResponse>(
    CONVERSATION_TURN_PATH,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export async function getConversationMessages(
  conversationId: string,
  afterId?: number,
): Promise<ConversationMessagesResponse> {
  const query = afterId === undefined ? "" : `?after_id=${afterId}`;
  return apiClient<ConversationMessagesResponse>(
    `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages${query}`,
  );
}
