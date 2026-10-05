import type {
    LeadHandoffQualification,
    LeadHandoffResponse,
} from "../../types/leadHandoff";

interface LeadHandoffPanelProps {
    handoff: LeadHandoffResponse;
}

const NOT_INFORMED = "Não informado";

const COMMERCIAL_INTENT_LABELS = {
    COMPRA: "Compra",
    ALUGUEL: "Aluguel",
    INVESTIMENTO: "Investimento",
    INDEFINIDO: NOT_INFORMED,
} as const;

const APPOINTMENT_TYPE_LABELS = {
    VISITA: "Visita",
    REUNIAO: "Reunião",
} as const;

const APPOINTMENT_STATUS_LABELS = {
    CONFIRMED: "Confirmado",
    CANCELLED: "Cancelado",
} as const;

function formatCurrency(value: string | null): string {
    if (value === null) {
        return NOT_INFORMED;
    }

    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
        maximumFractionDigits: 2,
    }).format(Number(value));
}

function formatBudget(
    qualification: LeadHandoffQualification,
): string {
    const { min_price: minPrice, max_price: maxPrice } = qualification;

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

function formatArea(value: string | null): string {
    if (value === null) {
        return NOT_INFORMED;
    }

    return `${new Intl.NumberFormat("pt-BR", {
        maximumFractionDigits: 2,
    }).format(Number(value))} m²`;
}

function formatAppointmentDate(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return NOT_INFORMED;
    }

    return new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Sao_Paulo",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    }).format(date);
}

function formatAppointmentTime(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return NOT_INFORMED;
    }

    return new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Sao_Paulo",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(date);
}

function HandoffItem({
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

function HandoffSection({
                            title,
                            children,
                        }: {
    title: string;
    children: React.ReactNode;
}) {
    return (
        <div className="border-t border-slate-200 pt-4 first:border-t-0 first:pt-0">
            <h3 className="text-sm font-semibold text-slate-800">
                {title}
            </h3>

            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
                {children}
            </dl>
        </div>
    );
}

export function LeadHandoffPanel({
                                     handoff,
                                 }: LeadHandoffPanelProps) {
    if (handoff.handoff_status !== "READY") {
        return null;
    }

    const {
        lead,
        qualification,
        property,
        appointment,
    } = handoff;

    const commercialIntent = qualification.commercial_intent
        ? COMMERCIAL_INTENT_LABELS[qualification.commercial_intent]
        : NOT_INFORMED;

    return (
        <section
            aria-labelledby="lead-handoff-title"
            className="border-b border-gray-200 bg-white px-4 py-4"
        >
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2
                        id="lead-handoff-title"
                        className="font-semibold text-gray-900"
                    >
                        Resumo para o Corretor
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                        Lead pronto para atendimento comercial.
                    </p>
                </div>

                <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700">
          {handoff.handoff_status}
        </span>
            </div>

            <div className="mt-5 space-y-5">
                <HandoffSection title="Lead">
                    <HandoffItem
                        label="Nome"
                        value={lead?.name ?? NOT_INFORMED}
                    />
                    <HandoffItem
                        label="Score"
                        value={lead ? `${lead.score} / 100` : NOT_INFORMED}
                    />
                    <HandoffItem
                        label="Classificação"
                        value={lead?.classification ?? NOT_INFORMED}
                    />
                </HandoffSection>

                <HandoffSection title="Qualificação">
                    <HandoffItem
                        label="Intenção"
                        value={commercialIntent}
                    />
                    <HandoffItem
                        label="Urgência"
                        value={formatUrgency(qualification.urgency_days)}
                    />
                    <HandoffItem
                        label="Região"
                        value={qualification.neighborhood ?? NOT_INFORMED}
                    />
                    <HandoffItem
                        label="Orçamento"
                        value={formatBudget(qualification)}
                    />
                    <HandoffItem
                        label="Quartos"
                        value={formatNumber(qualification.min_bedrooms)}
                    />
                    <HandoffItem
                        label="Banheiros"
                        value={formatNumber(qualification.min_bathrooms)}
                    />
                    <HandoffItem
                        label="Vagas"
                        value={formatNumber(qualification.min_parking_spaces)}
                    />
                    <HandoffItem
                        label="Área mínima"
                        value={formatArea(qualification.min_usable_area)}
                    />
                </HandoffSection>

                {property && (
                    <HandoffSection title="Imóvel">
                        <HandoffItem
                            label="Título"
                            value={property.title ?? NOT_INFORMED}
                        />
                        <HandoffItem
                            label="Bairro"
                            value={property.neighborhood ?? NOT_INFORMED}
                        />
                        <HandoffItem
                            label="Preço"
                            value={formatCurrency(property.price)}
                        />
                        <HandoffItem
                            label="Quartos"
                            value={formatNumber(property.bedrooms)}
                        />
                        <HandoffItem
                            label="Banheiros"
                            value={formatNumber(property.bathrooms)}
                        />
                        <HandoffItem
                            label="Vagas"
                            value={formatNumber(property.parking_spaces)}
                        />
                        <HandoffItem
                            label="Área"
                            value={formatArea(property.usable_area)}
                        />
                    </HandoffSection>
                )}

                <HandoffSection title="Agendamento">
                    <HandoffItem
                        label="Tipo"
                        value={
                            appointment
                                ? APPOINTMENT_TYPE_LABELS[
                                    appointment.appointment_type
                                    ]
                                : NOT_INFORMED
                        }
                    />
                    <HandoffItem
                        label="Data"
                        value={
                            appointment
                                ? formatAppointmentDate(appointment.scheduled_at)
                                : NOT_INFORMED
                        }
                    />
                    <HandoffItem
                        label="Horário"
                        value={
                            appointment
                                ? formatAppointmentTime(appointment.scheduled_at)
                                : NOT_INFORMED
                        }
                    />
                    <HandoffItem
                        label="Status"
                        value={
                            appointment
                                ? APPOINTMENT_STATUS_LABELS[appointment.status]
                                : NOT_INFORMED
                        }
                    />
                </HandoffSection>
            </div>
        </section>
    );
}
