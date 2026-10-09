import type { DashboardLeadSummary } from "../../types/dashboard";

interface LeadListProps {
  leads: DashboardLeadSummary[];
  selectedLeadId: number | null;
  onSelect: (leadId: number) => void;
}

const INTENT_LABELS = {
  COMPRA: "Compra",
  ALUGUEL: "Aluguel",
  INVESTIMENTO: "Investimento",
  INDEFINIDO: "Não informado",
} as const;

function formatDate(value: string | null): string {
  if (!value) {
    return "Não informado";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function LeadList({ leads, selectedLeadId, onSelect }: LeadListProps) {
  return (
    <ul className="divide-y divide-slate-200">
      {leads.map((lead) => (
        <li key={lead.lead_id}>
          <button
            type="button"
            aria-pressed={selectedLeadId === lead.lead_id}
            onClick={() => onSelect(lead.lead_id)}
            className={`w-full px-4 py-4 text-left transition hover:bg-blue-50 ${
              selectedLeadId === lead.lead_id
                ? "bg-blue-50 ring-1 ring-inset ring-blue-200"
                : "bg-white"
            }`}
          >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-slate-900">
                {lead.name ?? "Não informado"}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Última interação: {formatDate(lead.last_interaction_at)}
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
              {lead.classification}
            </span>
          </div>

          <dl className="mt-3 grid grid-cols-3 gap-2 text-xs">
            <div>
              <dt className="text-slate-500">Status</dt>
              <dd className="font-medium text-slate-800">{lead.status}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Intenção</dt>
              <dd className="font-medium text-slate-800">
                {lead.commercial_intent
                  ? INTENT_LABELS[lead.commercial_intent]
                  : "Não informado"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Score</dt>
              <dd className="font-medium text-blue-700">{lead.score} / 100</dd>
            </div>
          </dl>
          </button>
        </li>
      ))}
    </ul>
  );
}
