import type { LeadHandoffResponse } from "./leadHandoff";

export type CommercialIntent =
  | "COMPRA"
  | "ALUGUEL"
  | "INVESTIMENTO"
  | "INDEFINIDO";

export interface DashboardLeadSummary {
  lead_id: number;
  conversation_id: string;
  name: string | null;
  status: string;
  commercial_intent: CommercialIntent | null;
  score: number;
  classification: "FRIO" | "MORNO" | "QUENTE";
  last_interaction_at: string | null;
}

export interface DashboardLeadListResponse {
  leads: DashboardLeadSummary[];
}

export interface DashboardPreferences {
  urgency_days: number | null;
  neighborhood: string | null;
  min_price: string | null;
  max_price: string | null;
  min_bedrooms: number | null;
  min_bathrooms: number | null;
  min_parking_spaces: number | null;
  min_usable_area: number | null;
  semantic_preferences: string[];
}

export interface DashboardMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface DashboardProperty {
  id: number;
  external_id: string;
  title: string | null;
  description: string | null;
  neighborhood: string;
  price: string;
  bedrooms: number;
  bathrooms: number;
  parking_spaces: number | null;
  usable_area: number;
}

export interface DashboardAppointment {
  id: number;
  property_id: number | null;
  appointment_type: "VISITA" | "REUNIAO";
  scheduled_at: string;
  status: "CONFIRMED" | "CANCELLED";
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardLeadDetailResponse {
  lead: DashboardLeadSummary;
  preferences: DashboardPreferences;
  history: DashboardMessage[];
  recommended_properties: DashboardProperty[];
  selected_property: DashboardProperty | null;
  summary: LeadHandoffResponse;
  appointments: DashboardAppointment[];
}
