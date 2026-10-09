import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "../components/dashboard/Dashboard";
import {
  getDashboardLead,
  getDashboardLeads,
} from "../services/dashboardService";
import type {
  DashboardLeadDetailResponse,
  DashboardLeadSummary,
} from "../types/dashboard";

vi.mock("../services/dashboardService", () => ({
  getDashboardLeads: vi.fn(),
  getDashboardLead: vi.fn(),
}));

const mockedGetLeads = vi.mocked(getDashboardLeads);
const mockedGetLead = vi.mocked(getDashboardLead);

const lead: DashboardLeadSummary = {
  lead_id: 1,
  conversation_id: "conversation-1",
  name: "Rafael",
  status: "new",
  commercial_intent: "COMPRA",
  score: 75,
  classification: "QUENTE",
  last_interaction_at: "2026-10-05T14:30:00Z",
};

function detail(overrides: Partial<DashboardLeadDetailResponse> = {}): DashboardLeadDetailResponse {
  return {
    lead,
    preferences: {
      urgency_days: 30,
      neighborhood: "Boa Vista",
      min_price: "250000.00",
      max_price: "400000.00",
      min_bedrooms: 3,
      min_bathrooms: 2,
      min_parking_spaces: 1,
      min_usable_area: 70,
      semantic_preferences: ["varanda"],
    },
    history: [
      { id: 1, role: "user", content: "Quero comprar.", created_at: "2026-10-05T14:00:00Z" },
      { id: 2, role: "assistant", content: "Posso ajudar.", created_at: "2026-10-05T14:01:00Z" },
    ],
    recommended_properties: [{
      id: 10,
      external_id: "property-10",
      title: "Apartamento Boa Vista",
      description: "Descrição",
      neighborhood: "Boa Vista",
      price: "350000.00",
      bedrooms: 3,
      bathrooms: 2,
      parking_spaces: 1,
      usable_area: 70,
    }],
    selected_property: {
      id: 10,
      external_id: "property-10",
      title: "Apartamento Boa Vista",
      description: "Descrição",
      neighborhood: "Boa Vista",
      price: "350000.00",
      bedrooms: 3,
      bathrooms: 2,
      parking_spaces: 1,
      usable_area: 70,
    },
    summary: {
      conversation_id: "conversation-1",
      handoff_status: "NOT_READY",
      lead: null,
      qualification: {
        commercial_intent: "COMPRA",
        urgency_days: 30,
        neighborhood: "Boa Vista",
        min_price: "250000.00",
        max_price: "400000.00",
        min_bedrooms: 3,
        min_bathrooms: 2,
        min_parking_spaces: 1,
        min_usable_area: "70",
      },
      property: null,
      appointment: null,
    },
    appointments: [{
      id: 20,
      property_id: 10,
      appointment_type: "VISITA",
      scheduled_at: "2099-12-31T17:30:00Z",
      status: "CONFIRMED",
      notes: "Recepção",
      created_at: "2026-10-05T14:30:00Z",
      updated_at: "2026-10-05T14:30:00Z",
    }],
    ...overrides,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedGetLeads.mockResolvedValue({ leads: [lead] });
    mockedGetLead.mockResolvedValue(detail());
  });

  it("exibe loading, listagem e navegação para o Chat", async () => {
    let resolveList!: (value: { leads: DashboardLeadSummary[] }) => void;
    mockedGetLeads.mockReturnValue(new Promise((resolve) => { resolveList = resolve; }));

    render(<Dashboard />);

    expect(screen.getByText("Carregando leads...")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voltar ao atendimento" })).toHaveAttribute("href", "/");
    resolveList({ leads: [lead] });
    expect(await screen.findByText("Rafael")).toBeInTheDocument();
    expect(screen.getByText("new")).toBeInTheDocument();
    expect(screen.getByText("Compra")).toBeInTheDocument();
    expect(screen.getByText("75 / 100")).toBeInTheDocument();
    expect(screen.getByText("QUENTE")).toBeInTheDocument();
  });

  it("exibe empty state", async () => {
    mockedGetLeads.mockResolvedValue({ leads: [] });
    render(<Dashboard />);
    expect(await screen.findByText("Nenhum lead disponível.")).toBeInTheDocument();
  });

  it("exibe erro da lista e permite retry", async () => {
    mockedGetLeads
      .mockRejectedValueOnce(new Error("falha"))
      .mockResolvedValueOnce({ leads: [lead] });
    render(<Dashboard />);
    expect(await screen.findByText("Não foi possível carregar os leads.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByText("Rafael")).toBeInTheDocument();
    expect(mockedGetLeads).toHaveBeenCalledTimes(2);
  });

  it("seleciona lead e apresenta todas as seções do detalhe", async () => {
    render(<Dashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));

    expect(await screen.findByText("Identificação e qualificação")).toBeInTheDocument();
    expect(screen.getByText("R$ 250.000,00 — R$ 400.000,00")).toBeInTheDocument();
    expect(screen.getByText("varanda")).toBeInTheDocument();
    expect(screen.getByText("Quero comprar.")).toBeInTheDocument();
    expect(screen.getByText("Posso ajudar.")).toBeInTheDocument();
    expect(screen.getAllByText("Apartamento Boa Vista")).toHaveLength(2);
    expect(screen.getByText("Handoff ainda não está pronto. Os dados disponíveis permanecem nas seções acima.")).toBeInTheDocument();
    expect(screen.getByText("Visita")).toBeInTheDocument();
    expect(screen.getByText("Recepção")).toBeInTheDocument();
    expect(mockedGetLead).toHaveBeenCalledWith(1);
  });

  it("exibe erro do detalhe e permite retry", async () => {
    mockedGetLead
      .mockRejectedValueOnce(new Error("falha"))
      .mockResolvedValueOnce(detail());
    render(<Dashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    expect(await screen.findByText("Não foi possível carregar os detalhes do lead.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByText("Identificação e qualificação")).toBeInTheDocument();
    expect(mockedGetLead).toHaveBeenCalledTimes(2);
  });

  it("troca entre leads", async () => {
    const second = { ...lead, lead_id: 2, name: "Marina", conversation_id: "conversation-2" };
    mockedGetLeads.mockResolvedValue({ leads: [lead, second] });
    mockedGetLead
      .mockResolvedValueOnce(detail())
      .mockResolvedValueOnce(detail({ lead: second }));
    render(<Dashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    await screen.findByText("Identificação e qualificação");
    fireEvent.click(screen.getByRole("button", { name: /Marina/ }));
    await waitFor(() => expect(mockedGetLead).toHaveBeenLastCalledWith(2));
    expect(await screen.findAllByText("Marina")).not.toHaveLength(0);
  });

  it("ignora resposta antiga quando o lead mais recente responde primeiro", async () => {
    const second = { ...lead, lead_id: 2, name: "Marina", conversation_id: "conversation-2" };
    const firstRequest = deferred<DashboardLeadDetailResponse>();
    const secondRequest = deferred<DashboardLeadDetailResponse>();
    mockedGetLeads.mockResolvedValue({ leads: [lead, second] });
    mockedGetLead.mockImplementation((leadId) => (
      leadId === 1 ? firstRequest.promise : secondRequest.promise
    ));
    render(<Dashboard />);

    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    fireEvent.click(screen.getByRole("button", { name: /Marina/ }));
    secondRequest.resolve(detail({
      lead: second,
      history: [{ id: 20, role: "user", content: "Detalhe do Lead B", created_at: "2026-10-05T15:00:00Z" }],
    }));
    expect(await screen.findByText("Detalhe do Lead B")).toBeInTheDocument();

    firstRequest.resolve(detail({
      history: [{ id: 10, role: "user", content: "Detalhe do Lead A", created_at: "2026-10-05T14:00:00Z" }],
    }));
    await waitFor(() => {
      expect(screen.queryByText("Detalhe do Lead A")).not.toBeInTheDocument();
      expect(screen.getByText("Detalhe do Lead B")).toBeInTheDocument();
    });
  });

  it("ignora erro tardio de uma seleção antiga", async () => {
    const second = { ...lead, lead_id: 2, name: "Marina", conversation_id: "conversation-2" };
    const firstRequest = deferred<DashboardLeadDetailResponse>();
    const secondRequest = deferred<DashboardLeadDetailResponse>();
    mockedGetLeads.mockResolvedValue({ leads: [lead, second] });
    mockedGetLead.mockImplementation((leadId) => (
      leadId === 1 ? firstRequest.promise : secondRequest.promise
    ));
    render(<Dashboard />);

    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    fireEvent.click(screen.getByRole("button", { name: /Marina/ }));
    secondRequest.resolve(detail({
      lead: second,
      history: [{ id: 20, role: "user", content: "Lead B carregado", created_at: "2026-10-05T15:00:00Z" }],
    }));
    expect(await screen.findByText("Lead B carregado")).toBeInTheDocument();

    firstRequest.reject(new Error("falha tardia"));
    await waitFor(() => {
      expect(screen.queryByText("Não foi possível carregar os detalhes do lead.")).not.toBeInTheDocument();
      expect(screen.getByText("Lead B carregado")).toBeInTheDocument();
    });
  });

  it("mantém o loading da seleção atual quando a requisição antiga termina", async () => {
    const second = { ...lead, lead_id: 2, name: "Marina", conversation_id: "conversation-2" };
    const firstRequest = deferred<DashboardLeadDetailResponse>();
    const secondRequest = deferred<DashboardLeadDetailResponse>();
    mockedGetLeads.mockResolvedValue({ leads: [lead, second] });
    mockedGetLead.mockImplementation((leadId) => (
      leadId === 1 ? firstRequest.promise : secondRequest.promise
    ));
    render(<Dashboard />);

    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    fireEvent.click(screen.getByRole("button", { name: /Marina/ }));
    firstRequest.resolve(detail());
    await waitFor(() => {
      expect(screen.getByText("Carregando detalhes...")).toBeInTheDocument();
    });

    secondRequest.resolve(detail({ lead: second }));
    await screen.findByText("Identificação e qualificação");
    expect(screen.queryByText("Carregando detalhes...")).not.toBeInTheDocument();
  });

  it("mostra resumo READY pelo componente existente", async () => {
    mockedGetLead.mockResolvedValue(detail({
      summary: {
        conversation_id: "conversation-1",
        handoff_status: "READY",
        lead: { id: 1, name: "Rafael", score: 75, classification: "QUENTE" },
        qualification: detail().summary.qualification,
        property: null,
        appointment: {
          id: 20,
          appointment_type: "REUNIAO",
          scheduled_at: "2099-12-31T17:30:00Z",
          status: "CONFIRMED",
        },
      },
    }));
    render(<Dashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    expect(await screen.findByText("Lead pronto para atendimento comercial.")).toBeInTheDocument();
  });

  it("trata seções vazias e valores null", async () => {
    mockedGetLead.mockResolvedValue(detail({
      lead: { ...lead, name: null, commercial_intent: null, last_interaction_at: null },
      preferences: {
        urgency_days: null,
        neighborhood: null,
        min_price: null,
        max_price: null,
        min_bedrooms: null,
        min_bathrooms: null,
        min_parking_spaces: null,
        min_usable_area: null,
        semantic_preferences: [],
      },
      history: [],
      recommended_properties: [],
      selected_property: null,
      appointments: [],
    }));
    render(<Dashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /Rafael/ }));
    expect(await screen.findByText("Nenhuma mensagem disponível.")).toBeInTheDocument();
    expect(screen.getByText("Nenhum imóvel recomendado.")).toBeInTheDocument();
    expect(screen.getByText("Nenhum imóvel selecionado.")).toBeInTheDocument();
    expect(screen.getByText("Nenhum agendamento registrado.")).toBeInTheDocument();
    expect(screen.getAllByText("Não informado").length).toBeGreaterThan(0);
  });
});
