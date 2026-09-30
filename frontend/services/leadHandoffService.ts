import { apiClient } from "../lib/apiClient";
import type { LeadHandoffResponse } from "../types/leadHandoff";

const HANDOFFS_PATH = "/api/v1/handoffs";

export async function getLeadHandoff(
    conversationId: string,
): Promise<LeadHandoffResponse> {
    return apiClient<LeadHandoffResponse>(
        `${HANDOFFS_PATH}/${encodeURIComponent(conversationId)}`,
    );
}