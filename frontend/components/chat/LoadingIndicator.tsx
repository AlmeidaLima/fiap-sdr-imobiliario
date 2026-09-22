export function LoadingIndicator() {
  return (
    <div
      className="flex justify-start"
      role="status"
      aria-label="Agente está respondendo"
    >
      <div className="rounded-2xl bg-gray-100 px-4 py-3 text-sm text-gray-600">
        <span className="animate-pulse">
          Analisando sua mensagem...
        </span>
      </div>
    </div>
  );
}