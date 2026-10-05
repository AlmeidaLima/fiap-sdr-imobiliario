import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { Chat } from "../components/chat/Chat";
import { sendConversationTurn } from "../services/conversationService";

vi.mock("../services/conversationService", () => ({
  sendConversationTurn: vi.fn(),
}));

const mockedSendConversationTurn = vi.mocked(
  sendConversationTurn,
);

describe("Chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renderiza a mensagem inicial e o campo de envio", () => {
    render(<Chat />);

    expect(
        screen.getByText(
            "Olá! Eu sou a LIA, sua assistente imobiliária. Conte-me que tipo de imóvel você está procurando.",
        ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("textbox", {
        name: "Mensagem",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: "Dashboard" }),
    ).toHaveAttribute("href", "/dashboard");

    expect(
      screen.queryByRole("heading", {
        name: "Qualificação do lead",
      }),
    ).not.toBeInTheDocument();
  });

  test("envia a mensagem e exibe a resposta do backend", async () => {
    mockedSendConversationTurn.mockResolvedValue({
      conversation_id: "conversation-test",
      response: "Posso ajudar com isso. Qual é o seu orçamento máximo?",
      state: {
        conversation_id: "conversation-test",
        lead_name: null,
        commercial_intent: "COMPRA",
        urgency_days: null,
        accepted_meeting_or_visit: false,
        lead_score: 30,
        lead_classification: "FRIO",
        neighborhood: "Boa Vista",
        min_price: null,
        max_price: null,
        min_bedrooms: null,
        min_bathrooms: null,
        min_parking_spaces: null,
        min_usable_area: null,
        semantic_preferences: [],
        presented_property_ids: [],
        selected_property_id: null,
        appointment_stage: "NONE",
        appointment_type: null,
        appointment_date: null,
        appointment_time: null,
        appointment_id: null,
      },
      qualification: {
        qualified: false,
        missing_fields: ["max_price"],
        next_question:
          "Qual é o valor máximo que você pretende investir no imóvel?",
      },
      properties: [],
    });

    render(<Chat />);

    const input = screen.getByRole("textbox", {
      name: "Mensagem",
    });

    fireEvent.change(input, {
      target: {
        value: "Quero um apartamento em Boa Vista",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(
      screen.getByText(
        "Quero um apartamento em Boa Vista",
      ),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText(
          "Posso ajudar com isso. Qual é o seu orçamento máximo?",
        ),
      ).toBeInTheDocument();
    });

    expect(
      screen.queryByText(
        "Qual é o valor máximo que você pretende investir no imóvel?",
      ),
    ).not.toBeInTheDocument();

    expect(screen.getByText("30 / 100")).toBeInTheDocument();
    expect(screen.getByText("FRIO")).toBeInTheDocument();

    expect(
      mockedSendConversationTurn,
    ).toHaveBeenCalledTimes(1);

    expect(
      mockedSendConversationTurn,
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        message: "Quero um apartamento em Boa Vista",
        limit: 5,
      }),
    );
  });

  test("preserva o conversation_id entre múltiplos turnos", async () => {
    mockedSendConversationTurn
      .mockResolvedValueOnce({
        conversation_id: "conversation-test",
        response: "Qual é o seu orçamento máximo?",
        state: {
          conversation_id: "conversation-test",
          lead_name: null,
          commercial_intent: "COMPRA",
          urgency_days: null,
          accepted_meeting_or_visit: false,
          lead_score: 30,
          lead_classification: "FRIO",
          neighborhood: "Boa Vista",
          min_price: null,
          max_price: null,
          min_bedrooms: null,
          min_bathrooms: null,
          min_parking_spaces: null,
          min_usable_area: null,
          semantic_preferences: [],
          presented_property_ids: [],
          selected_property_id: null,
          appointment_stage: "NONE",
          appointment_type: null,
          appointment_date: null,
          appointment_time: null,
          appointment_id: null,
        },
        qualification: {
          qualified: false,
          missing_fields: ["max_price"],
          next_question:
            "Qual é o valor máximo que você pretende investir no imóvel?",
        },
        properties: [],
      })
      .mockResolvedValueOnce({
        conversation_id: "conversation-test",
        response: "Agora me diga quantos quartos você procura.",
        state: {
          conversation_id: "conversation-test",
          lead_name: null,
          commercial_intent: "COMPRA",
          urgency_days: null,
          accepted_meeting_or_visit: false,
          lead_score: 50,
          lead_classification: "MORNO",
          neighborhood: "Boa Vista",
          min_price: null,
          max_price: "700000",
          min_bedrooms: null,
          min_bathrooms: null,
          min_parking_spaces: null,
          min_usable_area: null,
          semantic_preferences: [],
          presented_property_ids: [],
          selected_property_id: null,
          appointment_stage: "NONE",
          appointment_type: null,
          appointment_date: null,
          appointment_time: null,
          appointment_id: null,
        },
        qualification: {
          qualified: false,
          missing_fields: ["min_bedrooms"],
          next_question:
            "Quantos quartos você procura?",
        },
        properties: [],
      });

    render(<Chat />);

    const input = screen.getByRole("textbox", {
      name: "Mensagem",
    });

    // Primeiro turno
    fireEvent.change(input, {
      target: {
        value: "Quero um apartamento em Boa Vista",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    await waitFor(() => {
      expect(
        mockedSendConversationTurn,
      ).toHaveBeenCalledTimes(1);
    });

    await screen.findByText(
      "Qual é o seu orçamento máximo?",
    );

    expect(screen.getByText("30 / 100")).toBeInTheDocument();

    // Segundo turno
    fireEvent.change(input, {
      target: {
        value: "Até 700 mil",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    await waitFor(() => {
      expect(
        mockedSendConversationTurn,
      ).toHaveBeenCalledTimes(2);
    });

    await screen.findByText(
      "Agora me diga quantos quartos você procura.",
    );

    expect(screen.getByText("50 / 100")).toBeInTheDocument();
    expect(screen.getByText("MORNO")).toBeInTheDocument();
    expect(screen.queryByText("30 / 100")).not.toBeInTheDocument();

    // Captura os requests enviados nos dois turnos
    const firstRequest =
      mockedSendConversationTurn.mock.calls[0][0];

    const secondRequest =
      mockedSendConversationTurn.mock.calls[1][0];

    // Valida as mensagens
    expect(firstRequest.message).toBe(
      "Quero um apartamento em Boa Vista",
    );

    expect(secondRequest.message).toBe(
      "Até 700 mil",
    );

    // O frontend deve gerar um conversation_id
    expect(
      firstRequest.conversation_id,
    ).toBeTruthy();

    // O mesmo ID deve ser reutilizado no segundo turno
    expect(
      secondRequest.conversation_id,
    ).toBe(firstRequest.conversation_id);
  });

  test("exibe os imóveis retornados após a qualificação", async () => {
  mockedSendConversationTurn.mockResolvedValue({
    conversation_id: "conversation-test",
    response: "Estas são as opções recuperadas para você.",
    state: {
      conversation_id: "conversation-test",
      lead_name: null,
      commercial_intent: "COMPRA",
      urgency_days: null,
      accepted_meeting_or_visit: false,
      lead_score: 50,
      lead_classification: "MORNO",
      neighborhood: "Boa Vista",
      min_price: null,
      max_price: "700000",
      min_bedrooms: 3,
      min_bathrooms: null,
      min_parking_spaces: null,
      min_usable_area: null,
      semantic_preferences: [],
      presented_property_ids: [1],
      selected_property_id: null,
      appointment_stage: "NONE",
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
    properties: [
      {
        id: 1,
        external_id: "property-001",
        title: "Apartamento com 3 quartos em Boa Vista",
        description: "Apartamento para venda em Curitiba",
        neighborhood: "Boa Vista",
        usable_area: 85,
        bedrooms: 3,
        bathrooms: 2,
        parking_spaces: 1,
        price: "671955.00",
        similarity_score: 0.88,
      },
    ],
  });

  render(<Chat />);

  const input = screen.getByRole("textbox", {
    name: "Mensagem",
  });

  fireEvent.change(input, {
    target: {
      value: "Quero 3 quartos",
    },
  });

  fireEvent.click(
    screen.getByRole("button", {
      name: "Enviar",
    }),
  );

  await waitFor(() => {
    expect(
      screen.getByText(
        "Estas são as opções recuperadas para você.",
      ),
    ).toBeInTheDocument();
  });

  expect(
    screen.getByText(
      "Apartamento com 3 quartos em Boa Vista",
    ),
  ).toBeInTheDocument();

  expect(
    screen.getByText("R$ 671.955"),
  ).toBeInTheDocument();

  expect(
    screen.getByText("3 quartos"),
  ).toBeInTheDocument();

  expect(
    screen.getByText("2 banheiros"),
  ).toBeInTheDocument();

  expect(
    screen.getByText("85 m²"),
  ).toBeInTheDocument();

  expect(
    screen.getByText("1 vaga"),
  ).toBeInTheDocument();

    expect(
        screen.getByText("88%"),
    ).toBeInTheDocument();

    expect(
        screen.getByText("Compatibilidade com sua busca"),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Encontrei alguns imóveis que combinam com sua busca.",
      ),
    ).not.toBeInTheDocument();
});
test("exibe a resposta do backend quando qualificado sem imóveis", async () => {
  mockedSendConversationTurn.mockResolvedValue({
    conversation_id: "conversation-test",
    response: "Não encontrei imóveis compatíveis com esses critérios.",
    state: {
      conversation_id: "conversation-test",
      lead_name: null,
      commercial_intent: "COMPRA",
      urgency_days: null,
      accepted_meeting_or_visit: false,
      lead_score: 50,
      lead_classification: "MORNO",
      neighborhood: "Boa Vista",
      min_price: null,
      max_price: "700000",
      min_bedrooms: 3,
      min_bathrooms: null,
      min_parking_spaces: null,
      min_usable_area: null,
      semantic_preferences: [],
      presented_property_ids: [],
      selected_property_id: null,
      appointment_stage: "NONE",
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
    properties: [],
  });

  render(<Chat />);

  fireEvent.change(
    screen.getByRole("textbox", { name: "Mensagem" }),
    { target: { value: "Quero 3 quartos" } },
  );

  fireEvent.click(
    screen.getByRole("button", { name: "Enviar" }),
  );

  expect(
    await screen.findByText(
      "Não encontrei imóveis compatíveis com esses critérios.",
    ),
  ).toBeInTheDocument();
});
test("exibe loading e bloqueia novo envio enquanto aguarda o backend", async () => {
  mockedSendConversationTurn.mockImplementation(
    () =>
      new Promise(() => {
        // Mantém a requisição pendente para validar o estado de loading.
      }),
  );

  render(<Chat />);

  const input = screen.getByRole("textbox", {
    name: "Mensagem",
  });

  const sendButton = screen.getByRole("button", {
    name: "Enviar",
  });

  fireEvent.change(input, {
    target: {
      value: "Quero um apartamento em Boa Vista",
    },
  });

  fireEvent.click(sendButton);

  await waitFor(() => {
    expect(
      screen.getByText("Analisando sua mensagem..."),
    ).toBeInTheDocument();
  });

  expect(input).toBeDisabled();

  expect(sendButton).toBeDisabled();

  expect(
    mockedSendConversationTurn,
  ).toHaveBeenCalledTimes(1);
});
test("exibe mensagem amigável quando ocorre erro na API", async () => {
  mockedSendConversationTurn.mockRejectedValue(
    new Error("Erro de comunicação com a API"),
  );

  render(<Chat />);

  const input = screen.getByRole("textbox", {
    name: "Mensagem",
  });

  fireEvent.change(input, {
    target: {
      value: "Quero um apartamento em Boa Vista",
    },
  });

  fireEvent.click(
    screen.getByRole("button", {
      name: "Enviar",
    }),
  );

  await waitFor(() => {
    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent(
      "Não foi possível enviar sua mensagem. Tente novamente.",
    );
  });

  expect(
    screen.queryByText("Analisando sua mensagem..."),
  ).not.toBeInTheDocument();

  expect(input).toBeEnabled();

  expect(
    screen.getByRole("button", {
      name: "Enviar",
    }),
  ).toBeDisabled();

  expect(
    mockedSendConversationTurn,
  ).toHaveBeenCalledTimes(1);
});
});
