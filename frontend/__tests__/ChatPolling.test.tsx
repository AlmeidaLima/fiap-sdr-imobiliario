import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { Chat } from "../components/chat/Chat";
import { ApiError } from "../lib/apiClient";
import {
  getConversationMessages,
  sendConversationTurn,
} from "../services/conversationService";
import type {
  ConversationMessagesResponse,
  ConversationTurnResponse,
} from "../types/conversation";


vi.mock("../services/conversationService", () => ({
  getConversationMessages: vi.fn(),
  sendConversationTurn: vi.fn(),
}));

const mockedGetMessages = vi.mocked(getConversationMessages);
const mockedSend = vi.mocked(sendConversationTurn);

function expectMessageOrder(...contents: string[]) {
  const pageText = document.body.textContent ?? "";
  const positions = contents.map((content) => pageText.indexOf(content));
  expect(positions.every((position) => position >= 0)).toBe(true);
  expect(positions).toEqual([...positions].sort((left, right) => left - right));
}

function turnResponse(): ConversationTurnResponse {
  return {
    conversation_id: "polling-conversation",
    user_message_id: 10,
    assistant_message_id: 12,
    response: "Resposta do turno",
    state: {
      conversation_id: "polling-conversation",
      lead_name: null,
      commercial_intent: null,
      urgency_days: null,
      accepted_meeting_or_visit: false,
      lead_score: 0,
      lead_classification: "FRIO",
      neighborhood: null,
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
      missing_fields: [],
      next_question: null,
    },
    properties: [],
  };
}

describe("Chat polling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    sessionStorage.setItem("lia_conversation_id", "polling-conversation");
  });

  afterEach(() => {
    vi.useRealTimers();
    sessionStorage.clear();
  });

  test("loads persisted history and replaces local greeting", async () => {
    mockedGetMessages.mockResolvedValue({
      messages: [{
        id: 1,
        role: "assistant",
        content: "Histórico persistido",
        created_at: "2026-10-05T12:00:00Z",
      }],
    });

    render(<Chat />);
    await act(async () => Promise.resolve());

    expect(screen.getByText("Histórico persistido")).toBeInTheDocument();
    expect(screen.queryByText(/Eu sou a LIA/)).not.toBeInTheDocument();
  });

  test("polling displays WEB message once and prevents overlapping polls", async () => {
    let resolvePoll: (value: { messages: [] }) => void = () => undefined;
    mockedGetMessages
      .mockResolvedValueOnce({ messages: [] })
      .mockImplementationOnce(() => new Promise((resolve) => {
        resolvePoll = resolve;
      }))
      .mockResolvedValueOnce({
        messages: [{
          id: 2,
          role: "assistant",
          content: "Follow-up WEB",
          created_at: "2026-10-05T12:00:00Z",
        }],
      });

    render(<Chat />);
    await act(async () => Promise.resolve());
    await act(async () => {
      vi.advanceTimersByTime(6000);
    });
    expect(mockedGetMessages).toHaveBeenCalledTimes(2);

    await act(async () => resolvePoll({ messages: [] }));
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });
    await act(async () => Promise.resolve());

    expect(screen.getAllByText("Follow-up WEB")).toHaveLength(1);
  });

  test("POST IDs deduplicate polling without losing intermediate message", async () => {
    mockedGetMessages
      .mockResolvedValueOnce({ messages: [] })
      .mockResolvedValueOnce({
        messages: [
          { id: 10, role: "user", content: "Minha mensagem", created_at: "2026-10-05T12:00:00Z" },
          { id: 11, role: "assistant", content: "Follow-up intermediário", created_at: "2026-10-05T12:00:01Z" },
          { id: 12, role: "assistant", content: "Resposta do turno", created_at: "2026-10-05T12:00:02Z" },
        ],
      });
    mockedSend.mockResolvedValue(turnResponse());
    render(<Chat />);
    await act(async () => Promise.resolve());

    fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
      target: { value: "Minha mensagem" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(screen.getByText("Resposta do turno")).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });
    await act(async () => Promise.resolve());

    expect(screen.getAllByText("Minha mensagem")).toHaveLength(1);
    expect(screen.getAllByText("Resposta do turno")).toHaveLength(1);
    expect(screen.getByText("Follow-up intermediário")).toBeInTheDocument();
    expectMessageOrder(
      "Minha mensagem",
      "Follow-up intermediário",
      "Resposta do turno",
    );
    expect(mockedGetMessages).toHaveBeenLastCalledWith(
      "polling-conversation",
      0,
    );
  });

  test("orders an intermediate WEB message discovered after POST", async () => {
    mockedGetMessages
      .mockResolvedValueOnce({ messages: [] })
      .mockResolvedValueOnce({
        messages: [{
          id: 11,
          role: "assistant",
          content: "WEB onze",
          created_at: "2026-10-05T12:00:01Z",
        }],
      });
    mockedSend.mockResolvedValue(turnResponse());
    render(<Chat />);
    await act(async () => Promise.resolve());

    fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
      target: { value: "Minha mensagem" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await act(async () => Promise.resolve());
    await act(async () => vi.advanceTimersByTime(3000));
    await act(async () => Promise.resolve());

    expectMessageOrder("Minha mensagem", "WEB onze", "Resposta do turno");
  });

  test("keeps order when polling finds WEB before POST completes", async () => {
    let resolvePost: (value: ConversationTurnResponse) => void = () => undefined;
    mockedGetMessages
      .mockResolvedValueOnce({ messages: [] })
      .mockResolvedValueOnce({
        messages: [
          { id: 10, role: "user", content: "Minha mensagem", created_at: "2026-10-05T12:00:00Z" },
          { id: 11, role: "assistant", content: "WEB onze", created_at: "2026-10-05T12:00:01Z" },
        ],
      });
    mockedSend.mockImplementation(() => new Promise((resolve) => {
      resolvePost = resolve;
    }));
    render(<Chat />);
    await act(async () => Promise.resolve());
    fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
      target: { value: "Minha mensagem" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await act(async () => vi.advanceTimersByTime(3000));
    await act(async () => Promise.resolve());
    await act(async () => resolvePost(turnResponse()));

    expect(screen.getAllByText("Minha mensagem")).toHaveLength(1);
    expectMessageOrder("Minha mensagem", "WEB onze", "Resposta do turno");
  });

  test("merges late initial history with an in-flight first turn", async () => {
    let resolveHistory: (value: ConversationMessagesResponse) => void = (
      () => undefined
    );
    mockedGetMessages.mockImplementationOnce(() => new Promise((resolve) => {
      resolveHistory = resolve;
    }));
    mockedSend.mockResolvedValue(turnResponse());
    render(<Chat />);
    fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
      target: { value: "Minha mensagem" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await act(async () => Promise.resolve());
    await act(async () => resolveHistory({
      messages: [{ id: 1, role: "assistant", content: "Histórico antigo", created_at: "2026-10-05T11:00:00Z" }],
    }));

    expect(screen.queryByText(/Eu sou a LIA/)).not.toBeInTheDocument();
    expectMessageOrder("Histórico antigo", "Minha mensagem", "Resposta do turno");
  });

  test("ignores a polling response from an unmounted conversation", async () => {
    let resolveOld: (value: { messages: Array<{ id: number; role: "assistant"; content: string; created_at: string }> }) => void = () => undefined;
    mockedGetMessages
      .mockImplementationOnce(() => new Promise((resolve) => { resolveOld = resolve; }))
      .mockResolvedValueOnce({ messages: [] });
    const first = render(<Chat />);
    first.unmount();
    sessionStorage.setItem("lia_conversation_id", "new-conversation");
    render(<Chat />);
    await act(async () => resolveOld({
      messages: [{ id: 99, role: "assistant", content: "Mensagem antiga", created_at: "2026-10-05T12:00:00Z" }],
    }));
    expect(screen.queryByText("Mensagem antiga")).not.toBeInTheDocument();
  });

  test("treats 404 for a fresh local id as empty history", async () => {
    sessionStorage.clear();
    mockedGetMessages.mockRejectedValue(new ApiError("missing", 404));
    render(<Chat />);
    await act(async () => Promise.resolve());
    expect(screen.getByText(/Eu sou a LIA/)).toBeInTheDocument();
    expect(screen.queryByText(/sincronizar novas mensagens/)).not.toBeInTheDocument();
  });

  test("replaces a restored session id that no longer exists", async () => {
    mockedGetMessages
      .mockRejectedValueOnce(new ApiError("missing", 404))
      .mockResolvedValueOnce({ messages: [] });
    render(<Chat />);
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());
    const replacement = sessionStorage.getItem("lia_conversation_id");
    expect(replacement).not.toBe("polling-conversation");
    expect(mockedGetMessages).toHaveBeenLastCalledWith(replacement, undefined);
    expect(screen.getByText(/Eu sou a LIA/)).toBeInTheDocument();
  });

  test("ignores a late POST response after replacing an invalid restored session", async () => {
    let rejectHistory: (reason: ApiError) => void = () => undefined;
    let resolveOldPost: (value: ConversationTurnResponse) => void = (
      () => undefined
    );
    mockedGetMessages
      .mockImplementationOnce(() => new Promise((_resolve, reject) => {
        rejectHistory = reject;
      }))
      .mockResolvedValueOnce({ messages: [] });
    mockedSend.mockImplementationOnce(() => new Promise((resolve) => {
      resolveOldPost = resolve;
    }));
    render(<Chat />);

    fireEvent.change(screen.getByRole("textbox", { name: "Mensagem" }), {
      target: { value: "Mensagem enviada em A" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await act(async () => rejectHistory(new ApiError("missing", 404)));
    await act(async () => Promise.resolve());

    const replacement = sessionStorage.getItem("lia_conversation_id");
    expect(replacement).not.toBe("polling-conversation");
    expect(mockedGetMessages).toHaveBeenLastCalledWith(replacement, undefined);

    const oldResponse = turnResponse();
    oldResponse.response = "RESPOSTA ANTIGA A";
    oldResponse.state.lead_score = 99;
    oldResponse.state.lead_classification = "QUENTE";
    oldResponse.qualification = {
      qualified: true,
      missing_fields: [],
      next_question: "QUALIFICACAO ANTIGA A",
    };
    oldResponse.properties = [{
      id: 999,
      external_id: "old-property-a",
      title: "IMOVEL ANTIGO A",
      description: "Não deve aparecer",
      neighborhood: "Sessão A",
      usable_area: 90,
      bedrooms: 3,
      bathrooms: 2,
      parking_spaces: 1,
      price: "900000",
      similarity_score: 0.99,
    }];
    await act(async () => resolveOldPost(oldResponse));

    expect(screen.queryByText("RESPOSTA ANTIGA A")).not.toBeInTheDocument();
    expect(screen.queryByText("99 / 100")).not.toBeInTheDocument();
    expect(screen.queryByText("QUENTE")).not.toBeInTheDocument();
    expect(screen.queryByText("IMOVEL ANTIGO A")).not.toBeInTheDocument();
    expect(screen.queryByText("QUALIFICACAO ANTIGA A")).not.toBeInTheDocument();
    expect(screen.getByText(/Eu sou a LIA/)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Mensagem" })).toBeEnabled();
    expect(sessionStorage.getItem("lia_conversation_id")).toBe(replacement);
  });

  test("temporary polling error keeps Chat usable and cleanup stops timer", async () => {
    mockedGetMessages
      .mockRejectedValueOnce(new Error("temporary"))
      .mockResolvedValue({ messages: [] });
    const { unmount } = render(<Chat />);
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText(/Não foi possível sincronizar/)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Mensagem" })).toBeEnabled();
    unmount();
    const callsBefore = mockedGetMessages.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(6000);
    });
    expect(mockedGetMessages).toHaveBeenCalledTimes(callsBefore);
  });
});
