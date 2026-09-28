import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Chat } from "../components/chat/Chat";
import { sendConversationTurn } from "../services/conversationService";
import type { ConversationTurnResponse } from "../types/conversation";
import type { PropertySearchResponse } from "../types/property";

vi.mock("../services/conversationService", () => ({
  sendConversationTurn: vi.fn(),
}));

const mockedSendConversationTurn = vi.mocked(sendConversationTurn);

const properties: PropertySearchResponse[] = [
  {
    id: 101,
    external_id: "external-101",
    title: "Apartamento Azul",
    description: null,
    neighborhood: "Boa Vista",
    usable_area: 70,
    bedrooms: 3,
    bathrooms: 2,
    parking_spaces: 1,
    price: "350000.00",
    similarity_score: 0.9,
  },
  {
    id: 202,
    external_id: "external-202",
    title: "Apartamento Verde",
    description: null,
    neighborhood: "Boa Vista",
    usable_area: 75,
    bedrooms: 3,
    bathrooms: 2,
    parking_spaces: 1,
    price: "380000.00",
    similarity_score: 0.85,
  },
];

function createResponse(
  selectedPropertyId: number | null = null,
): ConversationTurnResponse {
  return {
    conversation_id: "conversation-test",
    response: selectedPropertyId
      ? "Interesse registrado com sucesso."
      : "Encontrei dois imóveis para você.",
    state: {
      conversation_id: "conversation-test",
      lead_name: "Rafael",
      commercial_intent: "COMPRA",
      urgency_days: null,
      accepted_meeting_or_visit: false,
      lead_score: 50,
      lead_classification: "MORNO",
      neighborhood: "Boa Vista",
      min_price: null,
      max_price: "400000",
      min_bedrooms: 3,
      min_bathrooms: null,
      min_parking_spaces: null,
      min_usable_area: null,
      semantic_preferences: [],
      presented_property_ids: [101, 202],
      selected_property_id: selectedPropertyId,
      appointment_stage: selectedPropertyId ? "AWAITING_TYPE" : "NONE",
      appointment_type: null,
      appointment_date: null,
      appointment_time: null,
      appointment_id: null,
    },
    qualification: {
      qualified: true,
      missing_fields: [],
      next_question: null,
    },
    properties: selectedPropertyId ? [] : properties,
  };
}

function sendInitialMessage() {
  fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
    target: { value: "Quero três quartos" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

describe("seleção explícita de imóvel no Chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("envia o id estruturado e aguarda confirmação do backend", async () => {
    let resolveSelection: (response: ConversationTurnResponse) => void;
    const pendingSelection = new Promise<ConversationTurnResponse>((resolve) => {
      resolveSelection = resolve;
    });
    mockedSendConversationTurn
      .mockResolvedValueOnce(createResponse())
      .mockReturnValueOnce(pendingSelection);

    render(<Chat />);
    sendInitialMessage();
    expect(await screen.findByText("Apartamento Verde")).toBeInTheDocument();

    const firstRequest = mockedSendConversationTurn.mock.calls[0][0];
    const selectButton = screen.getByRole("button", {
      name: /Tenho interesse em Apartamento Verde/,
    });
    fireEvent.click(selectButton);

    expect(screen.queryByText("Selecionado")).not.toBeInTheDocument();
    expect(selectButton).toBeDisabled();
    fireEvent.click(selectButton);
    expect(mockedSendConversationTurn).toHaveBeenCalledTimes(2);

    const selectionRequest = mockedSendConversationTurn.mock.calls[1][0];
    expect(selectionRequest.conversation_id).toBe(firstRequest.conversation_id);
    expect(selectionRequest).toEqual({
      conversation_id: firstRequest.conversation_id,
      message: "Tenho interesse neste imóvel.",
      selected_property_id: 202,
      limit: 5,
    });
    expect(selectionRequest).not.toHaveProperty("state");
    expect(selectionRequest).not.toHaveProperty("presented_property_ids");

    resolveSelection!(createResponse(202));

    expect(await screen.findByText("Selecionado")).toBeInTheDocument();
    expect(screen.getByText("Interesse registrado com sucesso."))
      .toBeInTheDocument();
    expect(screen.getByText("50 / 100")).toBeInTheDocument();
    expect(screen.getByText("Não")).toBeInTheDocument();
  });

  test("erro não cria seleção falsa e preserva o último estado válido", async () => {
    mockedSendConversationTurn
      .mockResolvedValueOnce(createResponse())
      .mockResolvedValueOnce(createResponse(101))
      .mockRejectedValueOnce(new Error("Seleção inválida"));

    render(<Chat />);
    sendInitialMessage();
    expect(await screen.findByText("Apartamento Azul")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", {
      name: /Tenho interesse em Apartamento Azul/,
    }));
    expect(await screen.findByRole("button", {
      name: /Imóvel selecionado: Apartamento Azul/,
    })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", {
      name: /Tenho interesse em Apartamento Verde/,
    }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível selecionar o imóvel. Tente novamente.",
    );
    expect(screen.getByRole("button", {
      name: /Imóvel selecionado: Apartamento Azul/,
    })).toHaveTextContent("Selecionado");
    expect(screen.getByRole("button", {
      name: /Tenho interesse em Apartamento Verde/,
    })).toBeEnabled();
    expect(screen.queryByRole("button", {
      name: /Imóvel selecionado: Apartamento Verde/,
    })).not.toBeInTheDocument();
    expect(screen.getByText("50 / 100")).toBeInTheDocument();
  });
});
