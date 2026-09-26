import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PropertyList } from "../components/property/PropertyList";

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
});
