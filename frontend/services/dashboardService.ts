import { apiClient } from "../lib/apiClient";
import type {
  DashboardLeadDetailResponse,
  DashboardLeadListResponse,
} from "../types/dashboard";

const DASHBOARD_LEADS_PATH = "/api/v1/dashboard/leads";

export async function getDashboardLeads(): Promise<DashboardLeadListResponse> {
  return apiClient<DashboardLeadListResponse>(DASHBOARD_LEADS_PATH);
}

export async function getDashboardLead(
  leadId: number,
): Promise<DashboardLeadDetailResponse> {
  return apiClient<DashboardLeadDetailResponse>(
    `${DASHBOARD_LEADS_PATH}/${leadId}`,
  );
}
