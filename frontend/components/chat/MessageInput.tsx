"use client";

import { FormEvent, useState } from "react";

interface MessageInputProps {
  disabled?: boolean;
  onSend: (message: string) => void;
}

export function MessageInput({
  disabled = false,
  onSend,
}: MessageInputProps) {
  const [message, setMessage] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-3 border-t border-gray-200 p-4"
    >
      <input
        type="text"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        disabled={disabled}
        placeholder="Digite sua mensagem..."
        aria-label="Mensagem"
        className="flex-1 rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100"
      />

      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        Enviar
      </button>
    </form>
  );
}