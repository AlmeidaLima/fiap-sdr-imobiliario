import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Chat } from "../components/chat/Chat";
import { sendConversationTurn } from "../services/conversationService";
import type { ConversationTurnResponse } from "../types/conversation";
import type { PropertySearchResponse } from "../types/property";

vi.mock("../services/conversationService", () => ({
  sendConversationTurn: vi.fn(),
}));

const mockedSendConversationTurn = vi.mocked(sendConversationTurn);

const property: PropertySearchResponse = {
  id: 1,
  external_id: "property-001",
  title: "Imóvel anterior",
  description: "Apartamento para venda",
  neighborhood: "Boa Vista",
  usable_area: 85,
  bedrooms: 3,
  bathrooms: 2,
  parking_spaces: 1,
  price: "671955.00",
  similarity_score: 0.88,
};

function createResponse({
  response,
  qualified,
  properties = [],
  score = 30,
  classification = "FRIO",
}: {
  response: string;
  qualified: boolean;
  properties?: PropertySearchResponse[];
  score?: number;
  classification?: "FRIO" | "MORNO" | "QUENTE";
}): ConversationTurnResponse {
  return {
    conversation_id: "conversation-test",
    response,
    state: {
      conversation_id: "conversation-test",
      lead_name: null,
      commercial_intent: "COMPRA",
      urgency_days: null,
      accepted_meeting_or_visit: false,
      lead_score: score,
      lead_classification: classification,
      neighborhood: "Boa Vista",
      min_price: null,
      max_price: "700000",
      min_bedrooms: qualified ? 3 : null,
      min_bathrooms: null,
      min_parking_spaces: null,
      min_usable_area: null,
      semantic_preferences: [],
      presented_property_ids: properties.map((propertyItem) => propertyItem.id),
      selected_property_id: null,
      appointment_stage: "NONE",
      appointment_type: null,
      appointment_date: null,
      appointment_time: null,
      appointment_id: null,
    },
    qualification: {
      qualified,
      missing_fields: qualified ? [] : ["min_bedrooms"],
      next_question: qualified ? null : "Quantos quartos você procura?",
    },
    properties,
  };
}

function send(message: string) {
  const input = screen.getByRole("textbox", { name: "Mensagem" });
  fireEvent.change(input, { target: { value: message } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

describe("robustez dos estados do Chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("mantém o estado neutro quando a conversa ainda não está qualificada", async () => {
    mockedSendConversationTurn.mockResolvedValue(
      createResponse({
        response: "Preciso saber quantos quartos você procura.",
        qualified: false,
      }),
    );

    render(<Chat />);
    send("Quero comprar em Boa Vista");

    expect(
      await screen.findByText("Preciso saber quantos quartos você procura."),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "Nenhum imóvel encontrado para os critérios atuais.",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("As melhores opções aparecerão aqui."),
    ).toBeInTheDocument();
  });

  test("remove resultados antigos após busca qualificada sem imóveis", async () => {
    mockedSendConversationTurn
      .mockResolvedValueOnce(
        createResponse({
          response: "Encontrei uma opção.",
          qualified: true,
          properties: [property],
          score: 50,
          classification: "MORNO",
        }),
      )
      .mockResolvedValueOnce(
        createResponse({
          response: "Não encontrei opções para os novos critérios.",
          qualified: true,
          properties: [],
          score: 50,
          classification: "MORNO",
        }),
      );

    render(<Chat />);
    send("Quero três quartos");
    expect(await screen.findByText("Imóvel anterior")).toBeInTheDocument();

    send("Agora quero quatro quartos");
    expect(
      await screen.findByText("Não encontrei opções para os novos critérios."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Imóvel anterior")).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Nenhum imóvel encontrado para os critérios atuais.",
      ),
    ).toBeInTheDocument();
  });

  test("preserva dados no erro e recupera a conversa no próximo sucesso", async () => {
    const updatedProperty = {
      ...property,
      id: 2,
      external_id: "property-002",
      title: "Imóvel atualizado",
    };

    mockedSendConversationTurn
      .mockResolvedValueOnce(
        createResponse({
          response: "Primeira resposta.",
          qualified: true,
          properties: [property],
          score: 50,
          classification: "MORNO",
        }),
      )
      .mockRejectedValueOnce(new Error("Falha de rede"))
      .mockResolvedValueOnce(
        createResponse({
          response: "Conversa recuperada.",
          qualified: true,
          properties: [updatedProperty],
          score: 75,
          classification: "QUENTE",
        }),
      );

    render(<Chat />);

    send("Primeiro turno");
    expect(await screen.findByText("Primeira resposta.")).toBeInTheDocument();
    expect(screen.getByText("50 / 100")).toBeInTheDocument();
    expect(screen.getByText("Imóvel anterior")).toBeInTheDocument();

    send("Turno com erro");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível enviar sua mensagem. Tente novamente.",
    );
    expect(screen.getByText("Turno com erro")).toBeInTheDocument();
    expect(screen.getAllByText("Primeira resposta.")).toHaveLength(1);
    expect(screen.getByText("50 / 100")).toBeInTheDocument();
    expect(screen.getByText("Imóvel anterior")).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Mensagem" }),
    ).toBeEnabled();

    send("Terceiro turno");
    expect(await screen.findByText("Conversa recuperada.")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
    expect(screen.getByText("75 / 100")).toBeInTheDocument();
    expect(screen.getByText("QUENTE")).toBeInTheDocument();
    expect(screen.queryByText("50 / 100")).not.toBeInTheDocument();
    expect(screen.queryByText("Imóvel anterior")).not.toBeInTheDocument();
    expect(screen.getByText("Imóvel atualizado")).toBeInTheDocument();
    expect(mockedSendConversationTurn).toHaveBeenCalledTimes(3);
  });
});
