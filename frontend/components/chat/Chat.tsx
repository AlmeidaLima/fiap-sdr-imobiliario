"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { createAppointment } from "../../services/appointmentService";
import {
  getConversationMessages,
  sendConversationTurn,
} from "../../services/conversationService";
import { ApiError } from "../../lib/apiClient";
import { getLeadHandoff } from "../../services/leadHandoffService";

import type {
  ChatMessage,
  ConversationQualification,
  ConversationState,
  ConversationTurnResponse,
} from "../../types/conversation";
import type { PropertySearchResponse } from "../../types/property";
import type { LeadHandoffResponse } from "../../types/leadHandoff";
import { LeadQualificationPanel } from "../lead/LeadQualificationPanel";
import { LeadHandoffPanel } from "../lead/LeadHandoffPanel";
import { PropertyList } from "../property/PropertyList";
import { ChatHeader } from "./ChatHeader";
import { LoadingIndicator } from "./LoadingIndicator";
import { MessageInput } from "./MessageInput";
import { MessageList } from "./MessageList";

const INITIAL_MESSAGE: ChatMessage = {
  id: "initial-message",
  role: "assistant",
  content:
      "Olá! Eu sou a LIA, sua assistente imobiliária. Conte-me que tipo de imóvel você está procurando.",
};

const PROPERTY_SELECTION_MESSAGE = "Tenho interesse neste imóvel.";

const CONVERSATION_ID_STORAGE_KEY = "lia_conversation_id";
const MESSAGE_POLL_INTERVAL_MS = 3000;

interface ConversationSession {
  id: string;
  restored: boolean;
}

function getOrCreateConversationSession(): ConversationSession {
  if (typeof window === "undefined") {
    return { id: crypto.randomUUID(), restored: false };
  }

  const storedConversationId = sessionStorage.getItem(
    CONVERSATION_ID_STORAGE_KEY,
  );
  if (storedConversationId?.trim()) {
    return { id: storedConversationId, restored: true };
  }

  const conversationId = crypto.randomUUID();
  sessionStorage.setItem(CONVERSATION_ID_STORAGE_KEY, conversationId);
  return { id: conversationId, restored: false };
}

function mergeMessages(
  currentMessages: ChatMessage[],
  incomingMessages: ChatMessage[],
): ChatMessage[] {
  const persisted = new Map<number, ChatMessage>();
  const local = currentMessages.filter((message) => {
    if (message.persistedId !== undefined) {
      persisted.set(message.persistedId, message);
      return false;
    }
    return message.id !== INITIAL_MESSAGE.id;
  });

  for (const message of incomingMessages) {
    if (message.persistedId === undefined) {
      local.push(message);
      continue;
    }
    persisted.set(message.persistedId, {
      ...persisted.get(message.persistedId),
      ...message,
    });
  }

  const orderedPersisted = [...persisted.values()].sort((left, right) => {
    if (left.persistedCreatedAt && right.persistedCreatedAt) {
      const timestampComparison = left.persistedCreatedAt.localeCompare(
        right.persistedCreatedAt,
      );
      if (timestampComparison !== 0) {
        return timestampComparison;
      }
    }
    return (left.persistedId ?? 0) - (right.persistedId ?? 0);
  });

  if (orderedPersisted.length === 0) {
    return currentMessages;
  }
  return [...orderedPersisted, ...local];
}

function appointmentSuccessMessage(state: ConversationState): string {
  const type = state.appointment_type === "REUNIAO"
      ? "Reunião"
      : "Visita";

  const date = state.appointment_date
      ? state.appointment_date.split("-").reverse().join("/")
      : null;

  const time = state.appointment_time?.slice(0, 5) ?? null;

  return date && time
      ? `${type} agendada com sucesso para ${date} às ${time}.`
      : `${type} agendada com sucesso.`;
}

export function Chat() {
  const [conversationSession, setConversationSession] = useState(
    getOrCreateConversationSession,
  );
  const conversationId = conversationSession.id;
  const conversationIdRef = useRef(conversationId);

  const [messages, setMessages] = useState<ChatMessage[]>([
    INITIAL_MESSAGE,
  ]);

  const [properties, setProperties] = useState<
    PropertySearchResponse[]
  >([]);

  const [conversationState, setConversationState] = useState<
    ConversationState | null
  >(null);

  const [qualification, setQualification] = useState<
    ConversationQualification | null
  >(null);

  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appointmentError, setAppointmentError] = useState<string | null>(null);
  const [appointmentFeedback, setAppointmentFeedback] = useState<string | null>(
    null,
  );
  const [leadHandoff, setLeadHandoff] =
      useState<LeadHandoffResponse | null>(null);

  const [handoffError, setHandoffError] = useState<string | null>(null);
  const appointmentRequestInFlight = useRef(false);
  const persistedAppointments = useRef(new Set<string>());
  const handoffRequestInFlight = useRef(false);
  const loadedHandoffs = useRef(new Set<string>());
  const lastMessageIdRef = useRef(0);
  const seenMessageIdsRef = useRef(new Set<number>());
  const syncTokenRef = useRef(0);
  const pollingInFlightRef = useRef(false);
  const hasPersistedConversationRef = useRef(false);
  const hasStartedTurnRef = useRef(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  const syncMessages = useCallback(async (initial = false) => {
    if (!conversationId || pollingInFlightRef.current) {
      return;
    }
    const token = syncTokenRef.current;
    const requestedConversationId = conversationId;
    const afterId = initial ? undefined : lastMessageIdRef.current;
    pollingInFlightRef.current = true;

    try {
      const response = await getConversationMessages(
        requestedConversationId,
        afterId,
      );
      if (
        token !== syncTokenRef.current
        || requestedConversationId !== conversationId
      ) {
        return;
      }

      if (response.messages.length > 0) {
        hasPersistedConversationRef.current = true;
      }
      if (initial && !hasStartedTurnRef.current && response.state) {
        setConversationState(response.state);
      }
      if (initial && !hasStartedTurnRef.current && response.qualification) {
        setQualification(response.qualification);
      }
      for (const message of response.messages) {
        seenMessageIdsRef.current.add(message.id);
        lastMessageIdRef.current = Math.max(
          lastMessageIdRef.current,
          message.id,
        );
      }

      if (response.messages.length > 0) {
        setMessages((currentMessages) => mergeMessages(
          currentMessages,
          response.messages.map((message) => ({
            id: `persisted-${message.id}`,
            persistedId: message.id,
            persistedCreatedAt: message.created_at,
            role: message.role,
            content: message.content,
          })),
        ));
      }
      setSyncError(null);
    } catch (caughtError) {
      const isNotFound = (
        caughtError instanceof ApiError
        && caughtError.status === 404
        && !hasPersistedConversationRef.current
      );
      if (
        isNotFound
        && conversationSession.restored
        && token === syncTokenRef.current
      ) {
        const newConversationId = crypto.randomUUID();
        syncTokenRef.current += 1;
        conversationIdRef.current = newConversationId;
        sessionStorage.setItem(
          CONVERSATION_ID_STORAGE_KEY,
          newConversationId,
        );
        lastMessageIdRef.current = 0;
        seenMessageIdsRef.current.clear();
        hasPersistedConversationRef.current = false;
        hasStartedTurnRef.current = false;
        pollingInFlightRef.current = false;
        appointmentRequestInFlight.current = false;
        handoffRequestInFlight.current = false;
        persistedAppointments.current.clear();
        loadedHandoffs.current.clear();
        setMessages([INITIAL_MESSAGE]);
        setProperties([]);
        setConversationState(null);
        setQualification(null);
        setIsSending(false);
        setError(null);
        setAppointmentError(null);
        setAppointmentFeedback(null);
        setLeadHandoff(null);
        setHandoffError(null);
        setConversationSession({ id: newConversationId, restored: false });
        setSyncError(null);
      } else if (!isNotFound && token === syncTokenRef.current) {
        setSyncError("Não foi possível sincronizar novas mensagens.");
      }
    } finally {
      if (token === syncTokenRef.current) {
        pollingInFlightRef.current = false;
      }
    }
  }, [conversationId, conversationSession.restored]);

  useEffect(() => {
    void syncMessages(true);
    const timer = window.setInterval(() => {
      void syncMessages(false);
    }, MESSAGE_POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
      syncTokenRef.current += 1;
      pollingInFlightRef.current = false;
    };
  }, [syncMessages]);

  function isCurrentConversationRequest(
    token: number,
    requestConversationId: string,
  ): boolean {
    return (
      token === syncTokenRef.current
      && requestConversationId === conversationIdRef.current
    );
  }

  function applyResponse(
    response: ConversationTurnResponse,
    temporaryUserMessageId: string,
  ) {
    const appointmentFlowActive = response.state.appointment_stage !== "NONE";

    if (!appointmentFlowActive || response.properties.length > 0) {
      setProperties(response.properties);
    }
    setConversationState(response.state);
    setQualification(response.qualification);
    if (response.state.appointment_id === null) {
      setAppointmentFeedback(null);
    }

    const assistantAlreadySeen = seenMessageIdsRef.current.has(
      response.assistant_message_id,
    );
    seenMessageIdsRef.current.add(response.user_message_id);
    seenMessageIdsRef.current.add(response.assistant_message_id);
    hasPersistedConversationRef.current = true;

    const assistantMessage: ChatMessage = {
      id: `persisted-${response.assistant_message_id}`,
      persistedId: response.assistant_message_id,
      persistedCreatedAt: response.assistant_message_created_at,
      role: "assistant",
      content: response.response,
    };

    setMessages((currentMessages) => {
      const persistedUserAlreadyExists = currentMessages.some(
        (message) => message.persistedId === response.user_message_id,
      );
      const updated = currentMessages
        .filter((message) => (
          message.id !== temporaryUserMessageId || !persistedUserAlreadyExists
        ))
        .map((message) => (
          message.id === temporaryUserMessageId
            ? {
                ...message,
                id: `persisted-${response.user_message_id}`,
                persistedId: response.user_message_id,
                persistedCreatedAt: response.user_message_created_at,
              }
            : message
        ));
      return mergeMessages(
        updated,
        assistantAlreadySeen ? [] : [assistantMessage],
      );
    });
  }

  function appointmentOperationKey(state: ConversationState): string {
    return [
      conversationId,
      state.selected_property_id,
      state.appointment_type,
      state.appointment_date,
      state.appointment_time,
    ].join(":");
  }
  async function loadLeadHandoff(state: ConversationState) {
    if (!conversationId || state.appointment_id === null) {
      return;
    }

    const handoffKey = `${conversationId}:${state.appointment_id}`;

    if (
        handoffRequestInFlight.current
        || loadedHandoffs.current.has(handoffKey)
    ) {
      return;
    }

    handoffRequestInFlight.current = true;
    setHandoffError(null);

    try {
      const response = await getLeadHandoff(conversationId);

      setLeadHandoff(response);
      loadedHandoffs.current.add(handoffKey);
    } catch {
      setHandoffError(
          "O agendamento foi concluído, mas não foi possível carregar o resumo para o corretor.",
      );
    } finally {
      handoffRequestInFlight.current = false;
    }
  }
  async function persistConfirmedAppointment(state: ConversationState) {
    if (
      !conversationId
      || state.appointment_stage !== "CONFIRMED"
      || state.appointment_id !== null
    ) {
      return;
    }

    const operationKey = appointmentOperationKey(state);
    if (
      appointmentRequestInFlight.current
      || persistedAppointments.current.has(operationKey)
    ) {
      return;
    }

    appointmentRequestInFlight.current = true;
    setAppointmentError(null);

    try {
      const response = await createAppointment({
        conversation_id: conversationId,
      });

      persistedAppointments.current.add(operationKey);
      setConversationState(response.state);

      if (response.state.appointment_id !== null) {
        setAppointmentFeedback(
            appointmentSuccessMessage(response.state),
        );

        await loadLeadHandoff(response.state);
      }
    } catch {
      setAppointmentError(
        "N\u00e3o foi poss\u00edvel concluir o agendamento. Tente novamente.",
      );
    } finally {
      appointmentRequestInFlight.current = false;
    }
  }

  async function processResponse(
    response: ConversationTurnResponse,
    temporaryUserMessageId: string,
  ) {
    applyResponse(response, temporaryUserMessageId);
    await persistConfirmedAppointment(response.state);
  }

  async function handleSend(message: string) {
    if (isSending || !conversationId) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setIsSending(true);
    hasStartedTurnRef.current = true;
    setError(null);
    const requestToken = syncTokenRef.current;
    const requestConversationId = conversationId;

    try {
      const response = await sendConversationTurn({
        conversation_id: requestConversationId,
        message,
        limit: 5,
      });

      if (!isCurrentConversationRequest(
        requestToken,
        requestConversationId,
      )) {
        return;
      }
      await processResponse(response, userMessage.id);
    } catch {
      if (isCurrentConversationRequest(requestToken, requestConversationId)) {
        setError(
          "Não foi possível enviar sua mensagem. Tente novamente.",
        );
      }
    } finally {
      if (isCurrentConversationRequest(requestToken, requestConversationId)) {
        setIsSending(false);
      }
    }
  }

  async function handlePropertySelect(propertyId: number) {
    if (isSending || !conversationId) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: PROPERTY_SELECTION_MESSAGE,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);
    setIsSending(true);
    hasStartedTurnRef.current = true;
    setError(null);
    const requestToken = syncTokenRef.current;
    const requestConversationId = conversationId;

    try {
      const response = await sendConversationTurn({
        conversation_id: requestConversationId,
        message: PROPERTY_SELECTION_MESSAGE,
        selected_property_id: propertyId,
        limit: 5,
      });

      if (!isCurrentConversationRequest(
        requestToken,
        requestConversationId,
      )) {
        return;
      }
      await processResponse(response, userMessage.id);
    } catch {
      if (isCurrentConversationRequest(requestToken, requestConversationId)) {
        setError(
          "Não foi possível selecionar o imóvel. Tente novamente.",
        );
      }
    } finally {
      if (isCurrentConversationRequest(requestToken, requestConversationId)) {
        setIsSending(false);
      }
    }
  }

  async function handleAppointmentRetry() {
    if (isSending || !conversationState) {
      return;
    }

    setIsSending(true);
    await persistConfirmedAppointment(conversationState);
    setIsSending(false);
  }
  async function handleHandoffRetry() {
    if (
        isSending
        || !conversationState
        || conversationState.appointment_id === null
    ) {
      return;
    }

    const handoffKey =
        `${conversationId}:${conversationState.appointment_id}`;

    loadedHandoffs.current.delete(handoffKey);

    setIsSending(true);

    try {
      await loadLeadHandoff(conversationState);
    } finally {
      setIsSending(false);
    }
  }

  return (
      <section className="flex h-[80vh] w-full max-w-7xl flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <ChatHeader />

        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          {/* Painel da conversa */}
          <div className="flex min-h-0 flex-col border-b border-gray-200 md:w-2/5 md:border-r md:border-b-0">
            <div className="border-b border-gray-100 px-5 py-3">
              <h2 className="text-lg font-semibold text-gray-900">
                Conversa
              </h2>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50">
              <MessageList messages={messages} />

              {isSending && (
                  <div className="px-4 pb-3">
                    <LoadingIndicator />
                  </div>
              )}
            </div>

            {error && (
                <div
                    role="alert"
                    className="mx-4 mb-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700"
                >
                  {error}
                </div>
            )}

            {syncError && (
              <div
                role="status"
                className="mx-4 mb-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800"
              >
                <p>{syncError}</p>
                <button
                  type="button"
                  onClick={() => void syncMessages(false)}
                  className="mt-2 font-semibold underline"
                >
                  Tentar sincronizar novamente
                </button>
              </div>
            )}

            {appointmentError && (
              <div
                role="alert"
                className="mx-4 mb-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                <p>{appointmentError}</p>
                <button
                  type="button"
                  disabled={isSending}
                  onClick={handleAppointmentRetry}
                  className="mt-2 font-semibold underline disabled:opacity-50"
                >
                  Tentar novamente
                </button>
              </div>
            )}

            {appointmentFeedback && (
              <div
                role="status"
                className="mx-4 mb-3 rounded-lg bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800"
              >
                {appointmentFeedback}
              </div>
            )}
            {handoffError && (
                <div
                    role="alert"
                    className="mx-4 mb-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800"
                >
                  <p>{handoffError}</p>

                  <button
                      type="button"
                      disabled={isSending}
                      onClick={handleHandoffRetry}
                      className="mt-2 font-semibold underline disabled:opacity-50"
                  >
                    Tentar carregar resumo novamente
                  </button>
                </div>
            )}

            <MessageInput
                disabled={isSending || !conversationId}
                onSend={handleSend}
            />
          </div>

          {/* Painel dos imóveis */}
          <div className="min-h-0 flex-1 overflow-y-auto md:w-3/5">
            {conversationState && (
                <LeadQualificationPanel state={conversationState} />
            )}

            {leadHandoff && (
                <LeadHandoffPanel handoff={leadHandoff} />
            )}

            <PropertyList
              properties={properties}
              showNoResults={qualification?.qualified === true}
              onSelect={handlePropertySelect}
              selectedPropertyId={conversationState?.selected_property_id}
              appointmentPersisted={conversationState?.appointment_id != null}
              selectionDisabled={isSending}
            />
          </div>
        </div>
      </section>
  );
}
