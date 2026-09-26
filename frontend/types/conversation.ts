import type { PropertySearchResponse } from "./property";

export interface ConversationState {
  conversation_id: string;

  lead_name: string | null;

  commercial_intent:
    | "COMPRA"
    | "ALUGUEL"
    | "INVESTIMENTO"
    | "INDEFINIDO"
    | null;

  urgency_days: number | null;

  accepted_meeting_or_visit: boolean;

  lead_score: number;

  lead_classification: "FRIO" | "MORNO" | "QUENTE";

  neighborhood: string | null;

  min_price: string | null;
  max_price: string | null;

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
  state?: ConversationState | null;
  limit?: number;
}

export interface ConversationTurnResponse {
  conversation_id: string;
  response: string;
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
