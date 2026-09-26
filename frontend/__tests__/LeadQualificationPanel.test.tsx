import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LeadQualificationPanel } from "../components/lead/LeadQualificationPanel";
import type { ConversationState } from "../types/conversation";

function createState(
  overrides: Partial<ConversationState> = {},
): ConversationState {
  return {
    conversation_id: "conversation-test",
    lead_name: "Rafael",
    commercial_intent: "COMPRA",
    urgency_days: 30,
    accepted_meeting_or_visit: true,
    lead_score: 75,
    lead_classification: "QUENTE",
    neighborhood: "Boa Vista",
    min_price: "300000.00",
    max_price: "700000.00",
    min_bedrooms: 3,
    min_bathrooms: 2,
    min_parking_spaces: 1,
    min_usable_area: 70,
    semantic_preferences: [],
    ...overrides,
  };
}

describe("LeadQualificationPanel", () => {
  it("exibe o estado comercial completo recebido do backend", () => {
    render(<LeadQualificationPanel state={createState()} />);

    expect(screen.getByText("75 / 100")).toBeInTheDocument();
    expect(screen.getByText("QUENTE")).toBeInTheDocument();
    expect(screen.getByText("Compra")).toBeInTheDocument();
    expect(screen.getByText("30 dias")).toBeInTheDocument();
    expect(screen.getByText("Boa Vista")).toBeInTheDocument();
    expect(
      screen.getByText("R$ 300.000 a R$ 700.000"),
    ).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("70 m²")).toBeInTheDocument();
    expect(screen.getByText("Sim")).toBeInTheDocument();
  });

  it("apresenta campos ausentes sem renderizar valores técnicos", () => {
    const { container } = render(
      <LeadQualificationPanel
        state={createState({
          commercial_intent: null,
          urgency_days: null,
          neighborhood: null,
          min_price: null,
          max_price: null,
          min_bedrooms: null,
          min_bathrooms: null,
          min_parking_spaces: null,
          min_usable_area: null,
          accepted_meeting_or_visit: false,
        })}
      />,
    );

    expect(
      screen.getAllByText("Não informado").length,
    ).toBeGreaterThan(0);
    expect(container).not.toHaveTextContent("null");
    expect(container).not.toHaveTextContent("undefined");
    expect(screen.getByText("Não")).toBeInTheDocument();
  });

  it.each([
    ["300000.00", "700000.00", "R$ 300.000 a R$ 700.000"],
    ["300000.00", null, "A partir de R$ 300.000"],
    [null, "700000.00", "Até R$ 700.000"],
    [null, null, "Não informado"],
  ])(
    "formata orçamento mínimo %s e máximo %s",
    (minPrice, maxPrice, expected) => {
      render(
        <LeadQualificationPanel
          state={createState({
            min_price: minPrice,
            max_price: maxPrice,
          })}
        />,
      );

      expect(screen.getByText(expected)).toBeInTheDocument();
    },
  );

  it.each([
    [1, "1 dia"],
    [15, "15 dias"],
    [null, "Não informado"],
  ])("apresenta urgência %s", (urgencyDays, expected) => {
    render(
      <LeadQualificationPanel
        state={createState({ urgency_days: urgencyDays })}
      />,
    );

    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it.each(["FRIO", "MORNO", "QUENTE"] as const)(
    "apresenta a classificação %s recebida do backend",
    (classification) => {
      render(
        <LeadQualificationPanel
          state={createState({
            lead_score: 50,
            lead_classification: classification,
          })}
        />,
      );

      expect(screen.getByText(classification)).toBeInTheDocument();
      expect(screen.getByText("50 / 100")).toBeInTheDocument();
    },
  );
});
