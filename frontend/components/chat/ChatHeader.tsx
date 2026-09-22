export function ChatHeader() {
  return (
    <header className="border-b border-gray-200 px-5 py-4">
      <div className="flex items-center gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 font-semibold text-white"
          aria-hidden="true"
        >
          AI
        </div>

        <div>
          <h1 className="font-semibold text-gray-900">
            Agente SDR Imobiliário
          </h1>

          <p className="text-sm text-gray-500">
            Assistente virtual para encontrar seu imóvel
          </p>
        </div>
      </div>
    </header>
  );
}