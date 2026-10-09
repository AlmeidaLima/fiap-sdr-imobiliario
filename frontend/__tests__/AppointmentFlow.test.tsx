import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Chat } from "../components/chat/Chat";
import { createAppointment } from "../services/appointmentService";
import {
  getConversationMessages,
  sendConversationTurn,
} from "../services/conversationService";
import { getLeadHandoff } from "../services/leadHandoffService";
import type { LeadHandoffResponse } from "../types/leadHandoff";
import type { AppointmentCreateResponse } from "../types/appointment";
import type {
  ConversationState,
  ConversationTurnResponse,
} from "../types/conversation";

vi.mock("../services/appointmentService", () => ({
  createAppointment: vi.fn(),
}));
vi.mock("../services/conversationService", () => ({
  sendConversationTurn: vi.fn(),
  getConversationMessages: vi.fn(),
}));
vi.mock("../services/leadHandoffService", () => ({
  getLeadHandoff: vi.fn(),
}));

const mockedCreateAppointment = vi.mocked(createAppointment);
const mockedSendConversationTurn = vi.mocked(sendConversationTurn);
const mockedGetConversationMessages = vi.mocked(getConversationMessages);
const mockedGetLeadHandoff = vi.mocked(getLeadHandoff);
let nextMessageId = 1;

function createState(
  overrides: Partial<ConversationState> = {},
): ConversationState {
  return {
    conversation_id: "conversation-test",
    lead_name: "Rafael",
    commercial_intent: "COMPRA",
    urgency_days: 30,
    accepted_meeting_or_visit: false,
    lead_score: 75,
    lead_classification: "QUENTE",
    neighborhood: "Boa Vista",
    min_price: null,
    max_price: "400000",
    min_bedrooms: 3,
    min_bathrooms: null,
    min_parking_spaces: null,
    min_usable_area: null,
    semantic_preferences: [],
    presented_property_ids: [101],
    selected_property_id: 101,
    appointment_stage: "CONFIRMED",
    appointment_type: "VISITA",
    appointment_date: "2099-12-31",
    appointment_time: "14:30:00",
    appointment_id: null,
    ...overrides,
  };
}

function turnResponse(state: ConversationState): ConversationTurnResponse {
  const userMessageId = nextMessageId++;
  const assistantMessageId = nextMessageId++;
  return {
    conversation_id: state.conversation_id,
    user_message_id: userMessageId,
    assistant_message_id: assistantMessageId,
    response: "ConfirmaÃ§Ã£o recebida.",
    state,
    qualification: {
      qualified: true,
      missing_fields: [],
      next_question: null,
    },
    properties: [],
  };
}

function appointmentResponse(state: ConversationState): AppointmentCreateResponse {
  return {
    appointment: {
      id: state.appointment_id ?? 88,
      lead_id: 7,
      property_id: state.selected_property_id,
      appointment_type: state.appointment_type ?? "VISITA",
      scheduled_at: "2099-12-31T17:30:00Z",
      status: "CONFIRMED",
      idempotency_key: "stable-key",
      notes: null,
      created_at: "2026-09-28T12:00:00Z",
      updated_at: "2026-09-28T12:00:00Z",
    },
    state,
  };
}
function handoffResponse(
    overrides: Partial<LeadHandoffResponse> = {},
): LeadHandoffResponse {
  return {
    conversation_id: "conversation-existing",
    handoff_status: "READY",
    lead: {
      id: 7,
      name: "Rafael",
      score: 100,
      classification: "QUENTE",
    },
    qualification: {
      commercial_intent: "COMPRA",
      urgency_days: 30,
      neighborhood: "Boa Vista",
      min_price: null,
      max_price: "400000.00",
      min_bedrooms: 3,
      min_bathrooms: null,
      min_parking_spaces: null,
      min_usable_area: null,
    },
    property: {
      id: 101,
      external_id: "property-101",
      title: "Apartamento Boa Vista",
      neighborhood: "Boa Vista",
      price: "350000.00",
      bedrooms: 3,
      bathrooms: 2,
      parking_spaces: 1,
      usable_area: "75.00",
    },
    appointment: {
      id: 88,
      appointment_type: "VISITA",
      scheduled_at: "2099-12-31T17:30:00Z",
      status: "CONFIRMED",
    },
    ...overrides,
  };
}
function sendMessage(message = "confirmo") {
  fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
    target: { value: message },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

describe("persistÃªncia do agendamento no Chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    nextMessageId = 1;
    mockedGetConversationMessages.mockResolvedValue({ messages: [] });
    sessionStorage.clear();

    mockedGetLeadHandoff.mockResolvedValue(handoffResponse());
  });

  test("gera, salva e reutiliza o conversation_id da sessÃ£o", async () => {
    const first = render(<Chat />);

    await waitFor(() => {
      expect(sessionStorage.getItem("lia_conversation_id")).toBeTruthy();
    });
    const storedId = sessionStorage.getItem("lia_conversation_id");
    first.unmount();

    mockedSendConversationTurn.mockResolvedValue(
      turnResponse(createState({ appointment_stage: "AWAITING_DATE" })),
    );
    render(<Chat />);
    sendMessage("30/09/2099");

    await waitFor(() => {
      expect(mockedSendConversationTurn).toHaveBeenCalledWith(
        expect.objectContaining({ conversation_id: storedId }),
      );
    });
    expect(sessionStorage.getItem("lia_conversation_id")).toBe(storedId);
  });

  test("persiste CONFIRMED sem id e usa somente o state canônico  retornado", async () => {
    sessionStorage.setItem("lia_conversation_id", "conversation-existing");
    const confirmedState = createState();
    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });
    mockedSendConversationTurn.mockResolvedValue(turnResponse(confirmedState));
    mockedCreateAppointment.mockResolvedValue(
      appointmentResponse(persistedState),
    );

    const view = render(<Chat />);
    sendMessage();

    await waitFor(() => {
      expect(screen.getAllByText("100 / 100").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Sim")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Visita agendada com sucesso",
    );
    expect(mockedCreateAppointment).toHaveBeenCalledWith({
      conversation_id: "conversation-existing",
    });
    expect(mockedCreateAppointment.mock.calls[0][0]).toEqual({
      conversation_id: "conversation-existing",
    });

    view.rerender(<Chat />);
    expect(mockedCreateAppointment).toHaveBeenCalledTimes(1);
  });

  test("mostra finalização antes do appointment real e sucesso somente depois", async () => {
    let resolveAppointment: (response: AppointmentCreateResponse) => void;
    const pendingAppointment = new Promise<AppointmentCreateResponse>(
      (resolve) => {
        resolveAppointment = resolve;
      },
    );
    const confirmedState = createState();
    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });
    mockedSendConversationTurn.mockResolvedValue({
      ...turnResponse(confirmedState),
      response:
        "Dados do agendamento confirmados para 31/12/2099 às 14:30. "
        + "Finalizando o agendamento...",
    });
    mockedCreateAppointment.mockReturnValue(pendingAppointment);

    render(<Chat />);
    sendMessage();

    expect(await screen.findByText(/Finalizando o agendamento/))
      .toBeInTheDocument();
    expect(screen.queryByText(/Visita agendada com sucesso/))
      .not.toBeInTheDocument();

    resolveAppointment!(appointmentResponse(persistedState));

    expect(await screen.findByText(/Visita agendada com sucesso/))
      .toBeInTheDocument();
  });

  test.each([
    "NONE",
    "SELECTED",
    "AWAITING_TYPE",
    "AWAITING_DATE",
    "AWAITING_TIME",
    "AWAITING_CONFIRMATION",
    "CANCELLED",
  ] as const)("nÃ£o persiste appointment no estÃ¡gio %s", async (stage) => {
    mockedSendConversationTurn.mockResolvedValue(
      turnResponse(createState({ appointment_stage: stage })),
    );
    render(<Chat />);
    sendMessage();

    await screen.findByText("ConfirmaÃ§Ã£o recebida.");
    expect(mockedCreateAppointment).not.toHaveBeenCalled();
  });

  test("appointment_id existente impede nova persistÃªncia", async () => {
    mockedSendConversationTurn.mockResolvedValue(
      turnResponse(createState({ appointment_id: 88 })),
    );
    render(<Chat />);
    sendMessage();

    await screen.findByText("ConfirmaÃ§Ã£o recebida.");
    expect(mockedCreateAppointment).not.toHaveBeenCalled();
  });

  test("falha preserva o state confirmado e retry conclui sem repetir dados", async () => {
    const confirmedState = createState();
    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });
    mockedSendConversationTurn.mockResolvedValue(turnResponse(confirmedState));
    mockedCreateAppointment
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValueOnce(appointmentResponse(persistedState));

    render(<Chat />);
    sendMessage();

    const retry = await screen.findByRole("button", {
      name: "Tentar novamente",
    });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(screen.getByText("75 / 100")).toBeInTheDocument();
    expect(screen.getByText(/^N.o$/)).toBeInTheDocument();

    fireEvent.click(retry);

    await waitFor(() => {
      expect(screen.getAllByText("100 / 100").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Sim")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Visita agendada com sucesso",
    );
    expect(mockedCreateAppointment).toHaveBeenCalledTimes(2);
    expect(mockedSendConversationTurn).toHaveBeenCalledTimes(1);
  });
  test("não consulta handoff antes de existir appointment persistido", async () => {
    mockedSendConversationTurn.mockResolvedValue(
        turnResponse(
            createState({
              appointment_stage: "AWAITING_CONFIRMATION",
              appointment_id: null,
            }),
        ),
    );

    render(<Chat />);
    sendMessage();

    await waitFor(() => {
      expect(mockedSendConversationTurn).toHaveBeenCalledTimes(1);
    });

    expect(mockedCreateAppointment).not.toHaveBeenCalled();
    expect(mockedGetLeadHandoff).not.toHaveBeenCalled();
  });

  test("consulta handoff somente depois de receber appointment_id real", async () => {
    sessionStorage.setItem(
        "lia_conversation_id",
        "conversation-existing",
    );

    let resolveAppointment: (
        response: AppointmentCreateResponse,
    ) => void;

    const pendingAppointment =
        new Promise<AppointmentCreateResponse>((resolve) => {
          resolveAppointment = resolve;
        });

    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });

    mockedSendConversationTurn.mockResolvedValue(
        turnResponse(createState()),
    );

    mockedCreateAppointment.mockReturnValue(pendingAppointment);

    render(<Chat />);
    sendMessage();

    await waitFor(() => {
      expect(mockedCreateAppointment).toHaveBeenCalledTimes(1);
    });

    expect(mockedGetLeadHandoff).not.toHaveBeenCalled();

    resolveAppointment!(appointmentResponse(persistedState));

    await waitFor(() => {
      expect(mockedGetLeadHandoff).toHaveBeenCalledWith(
          "conversation-existing",
      );
    });

    expect(mockedGetLeadHandoff).toHaveBeenCalledTimes(1);

    expect(
        await screen.findByRole("heading", {
          name: "Resumo para o Corretor",
        }),
    ).toBeInTheDocument();

    expect(
        screen.getByText("Apartamento Boa Vista"),
    ).toBeInTheDocument();
  });

  test("falha do handoff preserva appointment persistido e permite retry sem recriar appointment", async () => {
    sessionStorage.setItem(
        "lia_conversation_id",
        "conversation-existing",
    );

    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });

    mockedSendConversationTurn.mockResolvedValue(
        turnResponse(createState()),
    );

    mockedCreateAppointment.mockResolvedValue(
        appointmentResponse(persistedState),
    );

    mockedGetLeadHandoff
        .mockRejectedValueOnce(new Error("handoff network error"))
        .mockResolvedValueOnce(handoffResponse());

    render(<Chat />);
    sendMessage();

    expect(
        await screen.findByText("100 / 100"),
    ).toBeInTheDocument();

    expect(screen.getByText("Sim")).toBeInTheDocument();

    expect(screen.getByRole("status")).toHaveTextContent(
        "Visita agendada com sucesso",
    );

    const retry = await screen.findByRole("button", {
      name: "Tentar carregar resumo novamente",
    });

    expect(mockedCreateAppointment).toHaveBeenCalledTimes(1);
    expect(mockedGetLeadHandoff).toHaveBeenCalledTimes(1);

    fireEvent.click(retry);

    expect(
        await screen.findByRole("heading", {
          name: "Resumo para o Corretor",
        }),
    ).toBeInTheDocument();

    expect(mockedGetLeadHandoff).toHaveBeenCalledTimes(2);

    // Retry do Handoff não pode persistir outro Appointment.
    expect(mockedCreateAppointment).toHaveBeenCalledTimes(1);

    // Também não deve repetir o turno da conversa.
    expect(mockedSendConversationTurn).toHaveBeenCalledTimes(1);
  });

  test("rerender não duplica consulta do handoff READY", async () => {
    sessionStorage.setItem(
        "lia_conversation_id",
        "conversation-existing",
    );

    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });

    mockedSendConversationTurn.mockResolvedValue(
        turnResponse(createState()),
    );

    mockedCreateAppointment.mockResolvedValue(
        appointmentResponse(persistedState),
    );

    const view = render(<Chat />);
    sendMessage();

    expect(
        await screen.findByRole("heading", {
          name: "Resumo para o Corretor",
        }),
    ).toBeInTheDocument();

    expect(mockedGetLeadHandoff).toHaveBeenCalledTimes(1);

    view.rerender(<Chat />);

    await waitFor(() => {
      expect(mockedGetLeadHandoff).toHaveBeenCalledTimes(1);
    });

    expect(mockedCreateAppointment).toHaveBeenCalledTimes(1);
  });

  test("NOT_READY não apresenta resumo como READY", async () => {
    const persistedState = createState({
      appointment_id: 88,
      accepted_meeting_or_visit: true,
      lead_score: 100,
    });

    mockedSendConversationTurn.mockResolvedValue(
        turnResponse(createState()),
    );

    mockedCreateAppointment.mockResolvedValue(
        appointmentResponse(persistedState),
    );

    mockedGetLeadHandoff.mockResolvedValue(
        handoffResponse({
          handoff_status: "NOT_READY",
          property: null,
          appointment: null,
        }),
    );

    render(<Chat />);
    sendMessage();

    await waitFor(() => {
      expect(mockedGetLeadHandoff).toHaveBeenCalledTimes(1);
    });

    expect(
        screen.queryByRole("heading", {
          name: "Resumo para o Corretor",
        }),
    ).not.toBeInTheDocument();

    expect(screen.getByRole("status")).toHaveTextContent(
        "Visita agendada com sucesso",
    );

    expect(mockedCreateAppointment).toHaveBeenCalledTimes(1);
  });
});
