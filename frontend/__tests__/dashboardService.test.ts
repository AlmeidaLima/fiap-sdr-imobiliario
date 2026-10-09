import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getDashboardLead,
  getDashboardLeads,
} from "../services/dashboardService";

describe("dashboardService", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("consulta a listagem no endpoint aprovado", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ leads: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getDashboardLeads();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/dashboard/leads",
      expect.objectContaining({ headers: { "Content-Type": "application/json" } }),
    );
  });

  it("consulta o detalhe pelo lead_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getDashboardLead(42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/dashboard/leads/42",
      expect.any(Object),
    );
  });

  it("propaga erro HTTP do cliente compartilhado", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));

    await expect(getDashboardLeads()).rejects.toMatchObject({ status: 500 });
  });
});
