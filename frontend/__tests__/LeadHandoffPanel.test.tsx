import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LeadHandoffPanel } from "../components/lead/LeadHandoffPanel";
import type { LeadHandoffResponse } from "../types/leadHandoff";

function createHandoff(
    overrides: Partial<LeadHandoffResponse> = {},
): LeadHandoffResponse {
    return {
        conversation_id: "conversation-handoff-test",
        handoff_status: "READY",
        lead: {
            id: 10,
            name: "Rafael",
            score: 100,
            classification: "QUENTE",
        },
        qualification: {
            commercial_intent: "COMPRA",
            urgency_days: 30,
            neighborhood: "Boa Vista",
            min_price: "250000.10",
            max_price: "400000.00",
            min_bedrooms: 3,
            min_bathrooms: 2,
            min_parking_spaces: 1,
            min_usable_area: "70.50",
        },
        property: {
            id: 8774,
            external_id: "property-external-id",
            title: "Apartamento com 3 dormitórios",
            neighborhood: "Boa Vista",
            price: "279990.45",
            bedrooms: 3,
            bathrooms: 2,
            parking_spaces: 1,
            usable_area: "73.00",
        },
        appointment: {
            id: 46,
            appointment_type: "VISITA",
            scheduled_at: "2099-12-31T17:30:00Z",
            status: "CONFIRMED",
        },
        ...overrides,
    };
}

describe("LeadHandoffPanel", () => {
    it("renderiza o resumo quando o backend retorna READY", () => {
        render(<LeadHandoffPanel handoff={createHandoff()} />);

        expect(
            screen.getByRole("heading", {
                name: "Resumo para o Corretor",
            }),
        ).toBeInTheDocument();

        expect(
            screen.getByText("Lead pronto para atendimento comercial."),
        ).toBeInTheDocument();

        expect(screen.getByText("READY")).toBeInTheDocument();
    });

    it("não renderiza o resumo quando o backend retorna NOT_READY", () => {
        const { container } = render(
            <LeadHandoffPanel
                handoff={createHandoff({
                    handoff_status: "NOT_READY",
                    appointment: null,
                    property: null,
                })}
            />,
        );

        expect(container).toBeEmptyDOMElement();
        expect(
            screen.queryByText("Resumo para o Corretor"),
        ).not.toBeInTheDocument();
    });

    it("exibe Lead, score e classificação recebidos do backend", () => {
        render(<LeadHandoffPanel handoff={createHandoff()} />);

        expect(screen.getByText("Rafael")).toBeInTheDocument();
        expect(screen.getByText("100 / 100")).toBeInTheDocument();
        expect(screen.getByText("QUENTE")).toBeInTheDocument();
    });

    it("exibe os dados de qualificação recebidos do backend", () => {
        render(<LeadHandoffPanel handoff={createHandoff()} />);

        expect(screen.getByText("Compra")).toBeInTheDocument();
        expect(screen.getByText("30 dias")).toBeInTheDocument();

        expect(
            screen.getAllByText("Boa Vista").length,
        ).toBeGreaterThan(0);

        expect(
            screen.getByText("R$ 250.000,10 a R$ 400.000,00"),
        ).toBeInTheDocument();

        expect(screen.getByText("70,5 m²")).toBeInTheDocument();
    });

    it("exibe o imóvel canônico para VISITA", () => {
        render(<LeadHandoffPanel handoff={createHandoff()} />);

        expect(
            screen.getByText("Apartamento com 3 dormitórios"),
        ).toBeInTheDocument();

        expect(
            screen.getByText("R$ 279.990,45"),
        ).toBeInTheDocument();

        expect(screen.getByText("73 m²")).toBeInTheDocument();
    });

    it("exibe fallback quando o título do imóvel é nulo", () => {
        render(
            <LeadHandoffPanel
                handoff={createHandoff({
                    property: {
                        ...createHandoff().property!,
                        title: null,
                    },
                })}
            />,
        );

        expect(screen.getByText("Não informado")).toBeInTheDocument();
    });

    it("exibe o Appointment persistido da VISITA", () => {
        render(<LeadHandoffPanel handoff={createHandoff()} />);

        expect(screen.getByText("Visita")).toBeInTheDocument();
        expect(screen.getByText("31/12/2099")).toBeInTheDocument();
        expect(screen.getByText("14:30")).toBeInTheDocument();
        expect(screen.getByText("Confirmado")).toBeInTheDocument();
    });

    it("renderiza REUNIAO sem imóvel", () => {
        render(
            <LeadHandoffPanel
                handoff={createHandoff({
                    property: null,
                    appointment: {
                        id: 47,
                        appointment_type: "REUNIAO",
                        scheduled_at: "2099-12-31T17:30:00Z",
                        status: "CONFIRMED",
                    },
                })}
            />,
        );

        expect(
            screen.getByRole("heading", {
                name: "Resumo para o Corretor",
            }),
        ).toBeInTheDocument();

        expect(screen.getByText("Reunião")).toBeInTheDocument();

        expect(
            screen.queryByRole("heading", { name: "Imóvel" }),
        ).not.toBeInTheDocument();

        expect(
            screen.getByRole("heading", { name: "Agendamento" }),
        ).toBeInTheDocument();
    });

    it("trata valores nulos sem exibir null ou undefined", () => {
        const { container } = render(
            <LeadHandoffPanel
                handoff={createHandoff({
                    lead: null,
                    qualification: {
                        commercial_intent: null,
                        urgency_days: null,
                        neighborhood: null,
                        min_price: null,
                        max_price: null,
                        min_bedrooms: null,
                        min_bathrooms: null,
                        min_parking_spaces: null,
                        min_usable_area: null,
                    },
                    property: null,
                    appointment: null,
                })}
            />,
        );

        expect(
            screen.getAllByText("Não informado").length,
        ).toBeGreaterThan(0);

        expect(container).not.toHaveTextContent("null");
        expect(container).not.toHaveTextContent("undefined");
    });

    it("preserva casas decimais recebidas como string na apresentação", () => {
        render(
            <LeadHandoffPanel
                handoff={createHandoff({
                    qualification: {
                        commercial_intent: "COMPRA",
                        urgency_days: 30,
                        neighborhood: "Boa Vista",
                        min_price: "250000.10",
                        max_price: "400000.99",
                        min_bedrooms: 3,
                        min_bathrooms: 2,
                        min_parking_spaces: 1,
                        min_usable_area: "70.25",
                    },
                    property: {
                        id: 8774,
                        external_id: "property-external-id",
                        title: "Apartamento teste",
                        neighborhood: "Boa Vista",
                        price: "279990.45",
                        bedrooms: 3,
                        bathrooms: 2,
                        parking_spaces: 1,
                        usable_area: "73.75",
                    },
                })}
            />,
        );

        expect(
            screen.getByText("R$ 250.000,10 a R$ 400.000,99"),
        ).toBeInTheDocument();

        expect(
            screen.getByText("R$ 279.990,45"),
        ).toBeInTheDocument();

        expect(screen.getByText("70,25 m²")).toBeInTheDocument();
        expect(screen.getByText("73,75 m²")).toBeInTheDocument();
    });
});
