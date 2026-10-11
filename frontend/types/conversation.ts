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

  presented_property_ids: number[];
  selected_property_id: number | null;

  appointment_stage:
    | "NONE"
    | "SELECTED"
    | "AWAITING_TYPE"
    | "AWAITING_DATE"
    | "AWAITING_TIME"
    | "AWAITING_CONFIRMATION"
    | "CONFIRMED"
    | "CANCELLED";
  appointment_type: "VISITA" | "REUNIAO" | null;
  appointment_date: string | null;
  appointment_time: string | null;
  appointment_id: number | null;
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
  selected_property_id?: number | null;
  limit?: number;
}

export interface ConversationTurnResponse {
  conversation_id: string;
  user_message_id: number;
  assistant_message_id: number;
  user_message_created_at?: string;
  assistant_message_created_at?: string;
  response: string;
  state: ConversationState;
  qualification: ConversationQualification;
  properties: PropertySearchResponse[];
}

export type ChatMessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  persistedId?: number;
  persistedCreatedAt?: string;
  role: ChatMessageRole;
  content: string;
}

export interface ConversationMessage {
  id: number;
  role: ChatMessageRole;
  content: string;
  created_at: string;
}

export interface ConversationMessagesResponse {
  messages: ConversationMessage[];
  state?: ConversationState;
  qualification?: ConversationQualification;
}
