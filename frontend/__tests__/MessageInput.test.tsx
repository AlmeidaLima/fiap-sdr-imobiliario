import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { MessageInput } from "../components/chat/MessageInput";

describe("MessageInput", () => {
  test("não envia mensagem vazia", () => {
    const onSend = vi.fn();

    render(<MessageInput onSend={onSend} />);

    const sendButton = screen.getByRole("button", {
      name: "Enviar",
    });

    expect(sendButton).toBeDisabled();

    fireEvent.click(sendButton);

    expect(onSend).not.toHaveBeenCalled();
  });

  test("envia a mensagem digitada", () => {
    const onSend = vi.fn();

    render(<MessageInput onSend={onSend} />);

    const input = screen.getByRole("textbox", {
      name: "Mensagem",
    });

    const sendButton = screen.getByRole("button", {
      name: "Enviar",
    });

    fireEvent.change(input, {
      target: {
        value: "Quero um apartamento em Boa Vista",
      },
    });

    expect(sendButton).toBeEnabled();

    fireEvent.click(sendButton);

    expect(onSend).toHaveBeenCalledTimes(1);

    expect(onSend).toHaveBeenCalledWith(
      "Quero um apartamento em Boa Vista",
    );
  });
});