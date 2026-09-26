"use client";

import { useState } from "react";

import { sendConversationTurn } from "../../services/conversationService";
import type {
  ChatMessage,
  ConversationQualification,
  ConversationState,
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

export function Chat() {
  const [conversationId] = useState(() => crypto.randomUUID());

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

  async function handleSend(message: string) {
    if (isSending) {
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

      setProperties(response.properties);
      setConversationState(response.state);
      setQualification(response.qualification);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.response,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch {
      setError(
        "Não foi possível enviar sua mensagem. Tente novamente.",
      );
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

            <MessageInput
                disabled={isSending}
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
            />
          </div>
        </div>
      </section>
  );
}
