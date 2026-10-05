export type LeadHandoffStatus = "READY" | "NOT_READY";

export type LeadHandoffAppointmentType = "VISITA" | "REUNIAO";

export type LeadHandoffAppointmentStatus = "CONFIRMED" | "CANCELLED";

export interface LeadHandoffLead {
    id: number;
    name: string | null;
    score: number;
    classification: "FRIO" | "MORNO" | "QUENTE";
}

export interface LeadHandoffQualification {
    commercial_intent:
        | "COMPRA"
        | "ALUGUEL"
        | "INVESTIMENTO"
        | "INDEFINIDO"
        | null;

    urgency_days: number | null;
    neighborhood: string | null;

    min_price: string | null;
    max_price: string | null;

    min_bedrooms: number | null;
    min_bathrooms: number | null;
    min_parking_spaces: number | null;

    min_usable_area: string | null;
}

export interface LeadHandoffProperty {
    id: number;
    external_id: string;
    title: string | null;
    neighborhood: string | null;

    price: string | null;

    bedrooms: number | null;
    bathrooms: number | null;
    parking_spaces: number | null;

    usable_area: string | null;
}

export interface LeadHandoffAppointment {
    id: number;
    appointment_type: LeadHandoffAppointmentType;
    scheduled_at: string;
    status: LeadHandoffAppointmentStatus;
}

export interface LeadHandoffResponse {
    conversation_id: string;
    handoff_status: LeadHandoffStatus;

    lead: LeadHandoffLead | null;
    qualification: LeadHandoffQualification;

    property: LeadHandoffProperty | null;
    appointment: LeadHandoffAppointment | null;
}
