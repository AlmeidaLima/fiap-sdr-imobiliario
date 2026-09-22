import type { ChatMessage } from "../../types/conversation";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({
  message,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
                ? "bg-blue-600 text-white shadow-sm"
                : "border border-indigo-100 bg-indigo-50 text-slate-800 shadow-sm"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}