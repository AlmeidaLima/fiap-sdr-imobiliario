import type { PropertySearchResponse } from "./property";

export interface ConversationState {
  conversation_id: string;

  lead_name: string | null;

  neighborhood: string | null;

  min_price: number | null;
  max_price: number | null;

  min_bedrooms: number | null;
  min_bathrooms: number | null;
  min_parking_spaces: number | null;
  min_usable_area: number | null;

  semantic_preferences: string[];
}

export interface ConversationQualification {
  qualified: boolean;
  missing_fields: string[];
  next_question: string | null;
}

export interface ConversationTurnRequest {
  conversation_id: string;
  message: string;
  limit?: number;
}

export interface ConversationTurnResponse {
  conversation_id: string;
  state: ConversationState;
  qualification: ConversationQualification;
  properties: PropertySearchResponse[];
}

export type ChatMessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
}