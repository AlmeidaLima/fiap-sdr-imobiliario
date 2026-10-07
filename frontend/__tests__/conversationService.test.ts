import { afterEach, describe, expect, test, vi } from "vitest";

import { getConversationMessages } from "../services/conversationService";


describe("conversationService messages", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("loads complete public history", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ messages: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getConversationMessages("conversation/test");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/conversations/conversation%2Ftest/messages",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  test("uses after_id for incremental polling", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ messages: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getConversationMessages("conversation", 42);

    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://localhost:8000/api/v1/conversations/conversation/messages?after_id=42",
    );
  });
});
