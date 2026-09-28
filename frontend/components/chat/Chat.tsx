"use client";

import { useRef, useState } from "react";

import { createAppointment } from "../../services/appointmentService";
import { sendConversationTurn } from "../../services/conversationService";
import type {
  ChatMessage,
  ConversationQualification,
  ConversationState,
  ConversationTurnResponse,
} from "../../types/conversation";
import type { PropertySearchResponse } from "../../types/property";
import { LeadQualificationPanel } from "../lead/LeadQualificationPanel";
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

function getOrCreateConversationId(): string {
  if (typeof window === "undefined") {
    return crypto.randomUUID();
  }

  const storedConversationId = sessionStorage.getItem(
    CONVERSATION_ID_STORAGE_KEY,
  );
  if (storedConversationId?.trim()) {
    return storedConversationId;
  }

  const conversationId = crypto.randomUUID();
  sessionStorage.setItem(CONVERSATION_ID_STORAGE_KEY, conversationId);
  return conversationId;
}

function appointmentSuccessMessage(state: ConversationState): string {
  const type = state.appointment_type === "REUNIAO" ? "ReuniÃ£o" : "Visita";
  const date = state.appointment_date
    ? state.appointment_date.split("-").reverse().join("/")
    : null;
  const time = state.appointment_time?.slice(0, 5) ?? null;

  return date && time
    ? `${type} agendada com sucesso para ${date} Ã s ${time}.`
    : `${type} agendada com sucesso.`;
}

export function Chat() {
  const [conversationId] = useState(getOrCreateConversationId);

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
  const appointmentRequestInFlight = useRef(false);
  const persistedAppointments = useRef(new Set<string>());

  function applyResponse(response: ConversationTurnResponse) {
    const appointmentFlowActive = response.state.appointment_stage !== "NONE";

    if (!appointmentFlowActive || response.properties.length > 0) {
      setProperties(response.properties);
    }
    setConversationState(response.state);
    setQualification(response.qualification);
    if (response.state.appointment_id === null) {
      setAppointmentFeedback(null);
    }

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: response.response,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      assistantMessage,
    ]);
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
        setAppointmentFeedback(appointmentSuccessMessage(response.state));
      }
    } catch {
      setAppointmentError(
        "N\u00e3o foi poss\u00edvel concluir o agendamento. Tente novamente.",
      );
    } finally {
      appointmentRequestInFlight.current = false;
    }
  }

  async function processResponse(response: ConversationTurnResponse) {
    applyResponse(response);
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
    setError(null);

    try {
      const response = await sendConversationTurn({
        conversation_id: conversationId,
        message,
        limit: 5,
      });

      await processResponse(response);
    } catch {
      setError(
        "Não foi possível enviar sua mensagem. Tente novamente.",
      );
    } finally {
      setIsSending(false);
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
    setError(null);

    try {
      const response = await sendConversationTurn({
        conversation_id: conversationId,
        message: PROPERTY_SELECTION_MESSAGE,
        selected_property_id: propertyId,
        limit: 5,
      });

      await processResponse(response);
    } catch {
      setError(
        "Não foi possível selecionar o imóvel. Tente novamente.",
      );
    } finally {
      setIsSending(false);
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
