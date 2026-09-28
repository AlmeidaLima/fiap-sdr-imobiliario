import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PropertyCard } from "../components/property/PropertyCard";
import type { PropertySearchResponse } from "../types/property";

function createProperty(
    overrides: Partial<PropertySearchResponse> = {},
): PropertySearchResponse {
    return {
        id: 1,
        external_id: "property-1",
        title: "Apartamento em Boa Vista",
        description: null,
        neighborhood: "Boa Vista",
        usable_area: 73,
        bedrooms: 1,
        bathrooms: 1,
        parking_spaces: 1,
        price: "279990.00",
        similarity_score: 0.88,
        ...overrides,
    };
}

describe("PropertyCard", () => {
    it("exibe atributos no singular quando a quantidade é 1", () => {
        render(
            <PropertyCard
                property={createProperty()}
            />,
        );

        expect(screen.getByText("1 quarto")).toBeInTheDocument();
        expect(screen.getByText("1 banheiro")).toBeInTheDocument();
        expect(screen.getByText("1 vaga")).toBeInTheDocument();
    });

    it("exibe atributos no plural quando a quantidade é maior que 1", () => {
        render(
            <PropertyCard
                property={createProperty({
                    bedrooms: 3,
                    bathrooms: 2,
                    parking_spaces: 2,
                })}
            />,
        );

        expect(screen.getByText("3 quartos")).toBeInTheDocument();
        expect(screen.getByText("2 banheiros")).toBeInTheDocument();
        expect(screen.getByText("2 vagas")).toBeInTheDocument();
    });

    it("formata como reais o preço serializado como string", () => {
        render(
            <PropertyCard
                property={createProperty({
                    price: "671955.00",
                })}
            />,
        );

        expect(screen.getByText("R$ 671.955")).toBeInTheDocument();
    });

    it("envia o id interno ao selecionar o imóvel", () => {
        const onSelect = vi.fn();
        render(
            <PropertyCard
                property={createProperty({
                    id: 42,
                    external_id: "external-999",
                })}
                onSelect={onSelect}
            />,
        );

        const button = screen.getByRole("button", {
            name: /Tenho interesse em Apartamento em Boa Vista/,
        });
        expect(button).toHaveTextContent("Tenho interesse");

        fireEvent.click(button);

        expect(onSelect).toHaveBeenCalledOnce();
        expect(onSelect).toHaveBeenCalledWith(42);
        expect(onSelect).not.toHaveBeenCalledWith("external-999");
    });

    it("apresenta o estado confirmado e desabilita a ação", () => {
        render(
            <PropertyCard
                property={createProperty()}
                onSelect={vi.fn()}
                isSelected
            />,
        );

        const button = screen.getByRole("button", {
            name: /Imóvel selecionado/,
        });
        expect(button).toHaveTextContent("Selecionado");
        expect(button).toBeDisabled();
        expect(button).toHaveAttribute("aria-pressed", "true");
    });

    it("apresenta visita agendada sem nova ação após persistência", () => {
        const onSelect = vi.fn();
        render(
            <PropertyCard
                property={createProperty()}
                onSelect={onSelect}
                isSelected
                appointmentPersisted
            />,
        );

        const button = screen.getByRole("button", {
            name: /Visita agendada/,
        });
        expect(button).toHaveTextContent("Visita agendada");
        expect(button).toBeDisabled();
        expect(screen.queryByText("Tenho interesse")).not.toBeInTheDocument();
        fireEvent.click(button);
        expect(onSelect).not.toHaveBeenCalled();
    });

    it("desabilita a ação durante o processamento", () => {
        render(
            <PropertyCard
                property={createProperty()}
                onSelect={vi.fn()}
                selectionDisabled
            />,
        );

        expect(screen.getByRole("button")).toBeDisabled();
    });
});
