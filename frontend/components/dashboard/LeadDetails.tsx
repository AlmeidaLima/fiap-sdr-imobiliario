import type {
  DashboardAppointment,
  DashboardLeadDetailResponse,
  DashboardPreferences,
  DashboardProperty,
} from "../../types/dashboard";
import { LeadHandoffPanel } from "../lead/LeadHandoffPanel";

const NOT_INFORMED = "Não informado";

const INTENT_LABELS = {
  COMPRA: "Compra",
  ALUGUEL: "Aluguel",
  INVESTIMENTO: "Investimento",
  INDEFINIDO: NOT_INFORMED,
} as const;

function formatCurrency(value: string | null): string {
  if (value === null) return NOT_INFORMED;
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value));
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatOptionalDate(value: string | null): string {
  return value === null ? NOT_INFORMED : formatDate(value);
}

function formatBudget(minPrice: string | null, maxPrice: string | null): string {
  if (minPrice && maxPrice) {
    return `${formatCurrency(minPrice)} — ${formatCurrency(maxPrice)}`;
  }
  if (minPrice) return `A partir de ${formatCurrency(minPrice)}`;
  if (maxPrice) return `Até ${formatCurrency(maxPrice)}`;
  return NOT_INFORMED;
}

function valueOrNotInformed(value: string | number | null): string {
  return value === null ? NOT_INFORMED : String(value);
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4">
      <h3 className="font-semibold text-slate-900">{title}</h3>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function Preferences({ preferences }: { preferences: DashboardPreferences }) {
  const budget = formatBudget(preferences.min_price, preferences.max_price);
  const rows = [
    ["Região", preferences.neighborhood ?? NOT_INFORMED],
    ["Orçamento", budget],
    ["Urgência", preferences.urgency_days === null
      ? NOT_INFORMED
      : `${preferences.urgency_days} dias`],
    ["Quartos", valueOrNotInformed(preferences.min_bedrooms)],
    ["Banheiros", valueOrNotInformed(preferences.min_bathrooms)],
    ["Vagas", valueOrNotInformed(preferences.min_parking_spaces)],
    ["Área mínima", preferences.min_usable_area === null
      ? NOT_INFORMED
      : `${preferences.min_usable_area} m²`],
    ["Outras preferências", preferences.semantic_preferences.length
      ? preferences.semantic_preferences.join(", ")
      : NOT_INFORMED],
  ];

  return (
    <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt className="text-xs font-medium text-slate-500">{label}</dt>
          <dd className="mt-1 text-sm font-semibold text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function PropertyItem({ property }: { property: DashboardProperty }) {
  return (
    <article className="rounded-lg border border-slate-200 p-3">
      <h4 className="font-semibold text-slate-900">
        {property.title ?? NOT_INFORMED}
      </h4>
      <p className="mt-1 text-sm text-slate-600">
        {property.neighborhood} · {formatCurrency(property.price)}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        {property.bedrooms} quartos · {property.bathrooms} banheiros · {property.usable_area} m²
      </p>
    </article>
  );
}

function AppointmentItem({ appointment }: { appointment: DashboardAppointment }) {
  return (
    <li className="rounded-lg border border-slate-200 p-3">
      <p className="font-semibold text-slate-900">
        {appointment.appointment_type === "VISITA" ? "Visita" : "Reunião"}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        {formatDate(appointment.scheduled_at)} · {appointment.status}
      </p>
      {appointment.notes && (
        <p className="mt-1 text-sm text-slate-500">{appointment.notes}</p>
      )}
    </li>
  );
}

export function LeadDetails({ detail }: { detail: DashboardLeadDetailResponse }) {
  return (
    <div className="space-y-4">
      <Section title="Identificação e qualificação">
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div><dt className="text-xs text-slate-500">Nome</dt><dd className="font-semibold">{detail.lead.name ?? NOT_INFORMED}</dd></div>
          <div><dt className="text-xs text-slate-500">Status</dt><dd className="font-semibold">{detail.lead.status}</dd></div>
          <div><dt className="text-xs text-slate-500">Intenção</dt><dd className="font-semibold">{detail.lead.commercial_intent ? INTENT_LABELS[detail.lead.commercial_intent] : NOT_INFORMED}</dd></div>
          <div><dt className="text-xs text-slate-500">Score</dt><dd className="font-semibold">{detail.lead.score} / 100</dd></div>
          <div><dt className="text-xs text-slate-500">Classificação</dt><dd className="font-semibold">{detail.lead.classification}</dd></div>
          <div><dt className="text-xs text-slate-500">Última interação</dt><dd className="font-semibold">{formatOptionalDate(detail.lead.last_interaction_at)}</dd></div>
        </dl>
      </Section>

      <Section title="Preferências"><Preferences preferences={detail.preferences} /></Section>

      <Section title="Histórico">
        {detail.history.length === 0 ? (
          <p className="text-sm text-slate-500">Nenhuma mensagem disponível.</p>
        ) : (
          <ol className="space-y-3">
            {detail.history.map((message) => (
              <li key={message.id} className="rounded-lg bg-slate-50 p-3">
                <div className="flex justify-between gap-3 text-xs text-slate-500">
                  <span>{message.role === "user" ? "Lead" : "Assistente"}</span>
                  <time>{formatDate(message.created_at)}</time>
                </div>
                <p className="mt-1 text-sm text-slate-800">{message.content}</p>
              </li>
            ))}
          </ol>
        )}
      </Section>

      <Section title="Imóveis recomendados">
        {detail.recommended_properties.length === 0 ? (
          <p className="text-sm text-slate-500">Nenhum imóvel recomendado.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {detail.recommended_properties.map((property) => (
              <PropertyItem key={property.id} property={property} />
            ))}
          </div>
        )}
      </Section>

      <Section title="Imóvel selecionado">
        {detail.selected_property ? (
          <PropertyItem property={detail.selected_property} />
        ) : (
          <p className="text-sm text-slate-500">Nenhum imóvel selecionado.</p>
        )}
      </Section>

      <Section title="Resumo para o corretor">
        {detail.summary.handoff_status === "READY" ? (
          <LeadHandoffPanel handoff={detail.summary} />
        ) : (
          <p className="text-sm text-slate-500">
            Handoff ainda não está pronto. Os dados disponíveis permanecem nas seções acima.
          </p>
        )}
      </Section>

      <Section title="Agendamentos">
        {detail.appointments.length === 0 ? (
          <p className="text-sm text-slate-500">Nenhum agendamento registrado.</p>
        ) : (
          <ul className="space-y-3">
            {detail.appointments.map((appointment) => (
              <AppointmentItem key={appointment.id} appointment={appointment} />
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}
