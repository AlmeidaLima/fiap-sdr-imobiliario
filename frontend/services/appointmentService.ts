import { apiClient } from "../lib/apiClient";
import type {
  AppointmentCreateRequest,
  AppointmentCreateResponse,
} from "../types/appointment";

const APPOINTMENTS_PATH = "/api/v1/appointments";

export async function createAppointment(
  request: AppointmentCreateRequest,
): Promise<AppointmentCreateResponse> {
  return apiClient<AppointmentCreateResponse>(APPOINTMENTS_PATH, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
