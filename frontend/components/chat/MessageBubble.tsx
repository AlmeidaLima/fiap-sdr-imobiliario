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
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}