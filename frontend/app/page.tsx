import { Chat } from "../components/chat/Chat";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <Chat />
    </main>
  );
}