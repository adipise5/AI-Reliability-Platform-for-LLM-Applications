import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, request } from "./client";

function mockFetchOnce(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  const fetchMock = vi.fn().mockResolvedValue(response as Response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("request", () => {
  it("returns the parsed JSON body on success", async () => {
    mockFetchOnce({ ok: true, status: 200, json: () => Promise.resolve({ hello: "world" }) });

    const result = await request<{ hello: string }>("http://api.test", "/things");

    expect(result).toEqual({ hello: "world" });
  });

  it("returns undefined for a 204 response", async () => {
    mockFetchOnce({ ok: true, status: 204, json: () => Promise.resolve(undefined) });

    const result = await request("http://api.test", "/things", { method: "DELETE" });

    expect(result).toBeUndefined();
  });

  it("throws an ApiError with the parsed error body on failure", async () => {
    mockFetchOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: () => Promise.resolve({ type: "not_found", message: "no such thing" }),
    });

    await expect(request("http://api.test", "/things/missing")).rejects.toMatchObject({
      status: 404,
      type: "not_found",
      message: "no such thing",
    });
  });

  it("attaches the bearer token and JSON content-type header", async () => {
    const fetchMock = mockFetchOnce({ ok: true, status: 200, json: () => Promise.resolve({}) });

    await request("http://api.test", "/things", { method: "POST", token: "tok123", body: { a: 1 } });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok123");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(init.body).toBe(JSON.stringify({ a: 1 }));
  });

  it("builds query params, skipping undefined values", async () => {
    const fetchMock = mockFetchOnce({ ok: true, status: 200, json: () => Promise.resolve([]) });

    await request("http://api.test", "/things", { query: { a: "1", b: undefined, c: 2 } });

    const [url] = fetchMock.mock.calls[0] as [string];
    const parsed = new URL(url);
    expect(parsed.searchParams.get("a")).toBe("1");
    expect(parsed.searchParams.has("b")).toBe(false);
    expect(parsed.searchParams.get("c")).toBe("2");
  });
});

describe("ApiError", () => {
  it("carries status, type, and message", () => {
    const error = new ApiError(409, { type: "conflict", message: "already exists" });

    expect(error.status).toBe(409);
    expect(error.type).toBe("conflict");
    expect(error.message).toBe("already exists");
  });
});
