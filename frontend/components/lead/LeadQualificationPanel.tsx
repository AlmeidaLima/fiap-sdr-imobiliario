import type { ConversationState } from "../../types/conversation";

interface LeadQualificationPanelProps {
  state: ConversationState;
}

const NOT_INFORMED = "Não informado";

const COMMERCIAL_INTENT_LABELS = {
  COMPRA: "Compra",
  ALUGUEL: "Aluguel",
  INVESTIMENTO: "Investimento",
  INDEFINIDO: NOT_INFORMED,
} as const;

function formatCurrency(value: string): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatBudget(
  minPrice: string | null,
  maxPrice: string | null,
): string {
  if (minPrice && maxPrice) {
    return `${formatCurrency(minPrice)} a ${formatCurrency(maxPrice)}`;
  }

  if (minPrice) {
    return `A partir de ${formatCurrency(minPrice)}`;
  }

  if (maxPrice) {
    return `Até ${formatCurrency(maxPrice)}`;
  }

  return NOT_INFORMED;
}

function formatUrgency(urgencyDays: number | null): string {
  if (urgencyDays === null) {
    return NOT_INFORMED;
  }

  return `${urgencyDays} ${urgencyDays === 1 ? "dia" : "dias"}`;
}

function formatNumber(value: number | null): string {
  return value === null ? NOT_INFORMED : String(value);
}

function QualificationItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-semibold text-slate-900">
        {value}
      </dd>
    </div>
  );
}

export function LeadQualificationPanel({
  state,
}: LeadQualificationPanelProps) {
  const commercialIntent = state.commercial_intent
    ? COMMERCIAL_INTENT_LABELS[state.commercial_intent]
    : NOT_INFORMED;

  return (
    <section
      aria-labelledby="lead-qualification-title"
      className="border-b border-gray-200 bg-white px-4 py-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2
          id="lead-qualification-title"
          className="font-semibold text-gray-900"
        >
          Qualificação do lead
        </h2>

        <div className="flex items-center gap-2 text-sm">
          <span className="font-semibold text-blue-700">
            {state.lead_score} / 100
          </span>
          <span className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-700">
            {state.lead_classification}
          </span>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
        <QualificationItem label="Intenção" value={commercialIntent} />
        <QualificationItem
          label="Urgência"
          value={formatUrgency(state.urgency_days)}
        />
        <QualificationItem
          label="Região"
          value={state.neighborhood ?? NOT_INFORMED}
        />
        <QualificationItem
          label="Orçamento"
          value={formatBudget(state.min_price, state.max_price)}
        />
        <QualificationItem
          label="Quartos"
          value={formatNumber(state.min_bedrooms)}
        />
        <QualificationItem
          label="Banheiros"
          value={formatNumber(state.min_bathrooms)}
        />
        <QualificationItem
          label="Vagas"
          value={formatNumber(state.min_parking_spaces)}
        />
        <QualificationItem
          label="Área mínima"
          value={
            state.min_usable_area === null
              ? NOT_INFORMED
              : `${state.min_usable_area} m²`
          }
        />
        <QualificationItem
          label="Aceitou reunião/visita"
          value={state.accepted_meeting_or_visit ? "Sim" : "Não"}
        />
      </dl>
    </section>
  );
}
