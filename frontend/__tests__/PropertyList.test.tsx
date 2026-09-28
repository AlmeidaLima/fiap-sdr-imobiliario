import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PropertyList } from "../components/property/PropertyList";
import type { PropertySearchResponse } from "../types/property";

const properties: PropertySearchResponse[] = [
    {
        id: 10,
        external_id: "external-first",
        title: "Primeiro imóvel",
        description: null,
        neighborhood: "Boa Vista",
        usable_area: 70,
        bedrooms: 2,
        bathrooms: 1,
        parking_spaces: 1,
        price: "300000.00",
        similarity_score: 0.9,
    },
    {
        id: 20,
        external_id: "external-second",
        title: "Segundo imóvel",
        description: null,
        neighborhood: "Cabral",
        usable_area: 80,
        bedrooms: 3,
        bathrooms: 2,
        parking_spaces: 1,
        price: "400000.00",
        similarity_score: 0.8,
    },
];

describe("PropertyList", () => {
    it("exibe orientação enquanto ainda não existem imóveis", () => {
        render(<PropertyList properties={[]} />);

        expect(
            screen.getByText("Encontre seu imóvel ideal"),
        ).toBeInTheDocument();

        expect(
            screen.getByText(
                "As melhores opções aparecerão aqui.",
            ),
        ).toBeInTheDocument();

        expect(
            screen.queryByText(
                "Nenhum imóvel encontrado para os critérios atuais.",
            ),
        ).not.toBeInTheDocument();
    });

    it("exibe o estado de busca sem resultados", () => {
        render(<PropertyList properties={[]} showNoResults />);

        expect(
            screen.getByText(
                "Nenhum imóvel encontrado para os critérios atuais.",
            ),
        ).toBeInTheDocument();
    });

    it("preserva a ordem e propaga o id do card selecionado", () => {
        const onSelect = vi.fn();
        render(
            <PropertyList
                properties={properties}
                onSelect={onSelect}
            />,
        );

        const firstTitle = screen.getByText("Primeiro imóvel");
        const secondTitle = screen.getByText("Segundo imóvel");
        expect(
            firstTitle.compareDocumentPosition(secondTitle)
            & Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();

        fireEvent.click(screen.getByRole("button", {
            name: /Tenho interesse em Segundo imóvel/,
        }));

        expect(onSelect).toHaveBeenCalledOnce();
        expect(onSelect).toHaveBeenCalledWith(20);
        expect(onSelect).not.toHaveBeenCalledWith("external-second");
    });

    it("marca somente o imóvel confirmado pelo estado recebido", () => {
        render(
            <PropertyList
                properties={properties}
                onSelect={vi.fn()}
                selectedPropertyId={20}
            />,
        );

        expect(screen.getByRole("button", {
            name: /Imóvel selecionado: Segundo imóvel/,
        })).toHaveTextContent("Selecionado");
        expect(screen.getByRole("button", {
            name: /Tenho interesse em Primeiro imóvel/,
        })).toBeEnabled();
    });
    it("marca somente o imóvel agendado após existir appointment", () => {
        render(
            <PropertyList
                properties={properties}
                onSelect={vi.fn()}
                selectedPropertyId={20}
                appointmentPersisted
            />,
        );

        expect(screen.getByRole("button", {
            name: /Visita agendada: Segundo imóvel/,
        })).toHaveTextContent("Visita agendada");
        expect(screen.getByRole("button", {
            name: /Tenho interesse em Primeiro imóvel/,
        })).toBeEnabled();
    });
});
