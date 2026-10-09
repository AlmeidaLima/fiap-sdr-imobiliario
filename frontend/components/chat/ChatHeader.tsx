import Link from "next/link";

export function ChatHeader() {
  return (
      <header className="border-b border-indigo-500 bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
          <div
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/15 text-sm font-bold text-white ring-1 ring-white/30"
              aria-hidden="true"
          >
            LIA
          </div>

          <div className="min-w-0">
            <h1 className="text-white">
              <span className="font-semibold">LIA</span>{" "}
              <span className="font-normal">— Inteligência para Leads Imobiliários</span>
            </h1>

            <p className="text-sm text-blue-100">
              Sua assistente inteligente para encontrar o imóvel ideal
            </p>
          </div>
          </div>

          <Link
              href="/dashboard"
              className="shrink-0 rounded-lg bg-white/15 px-3 py-2 text-sm font-semibold text-white ring-1 ring-white/30 hover:bg-white/25"
          >
            Dashboard
          </Link>
        </div>
      </header>
  );
}
