import type { ConversationState } from "./conversation";

export interface AppointmentResponse {
  id: number;
  lead_id: number;
  property_id: number | null;
  appointment_type: "VISITA" | "REUNIAO";
  scheduled_at: string;
  status: "CONFIRMED" | "CANCELLED";
  idempotency_key: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreateRequest {
  conversation_id: string;
}

export interface AppointmentCreateResponse {
  appointment: AppointmentResponse;
  state: ConversationState;
}
