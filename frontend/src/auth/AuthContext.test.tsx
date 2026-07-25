import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as authApi from "../api/auth";
import { AuthProvider, useAuth } from "./AuthContext";

vi.mock("../api/auth");

function Probe() {
  const { session, logout } = useAuth();
  return (
    <div>
      <span data-testid="email">{session?.email ?? "none"}</span>
      <button onClick={logout}>logout</button>
    </div>
  );
}

function LoginButton() {
  const { login } = useAuth();
  return <button onClick={() => login("a@b.com", "pw")}>login</button>;
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AuthProvider", () => {
  it("starts with no session when localStorage is empty", () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(screen.getByTestId("email")).toHaveTextContent("none");
  });

  it("stores the session after a successful login", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: "tok-123",
      token_type: "bearer",
      expires_in: 3600,
    });
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <LoginButton />
        <Probe />
      </AuthProvider>,
    );

    await act(() => user.click(screen.getByText("login")));

    expect(screen.getByTestId("email")).toHaveTextContent("a@b.com");
    expect(JSON.parse(localStorage.getItem("arp.session")!).token).toBe("tok-123");
  });

  it("clears the session on logout", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: "tok-123",
      token_type: "bearer",
      expires_in: 3600,
    });
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <LoginButton />
        <Probe />
      </AuthProvider>,
    );

    await act(() => user.click(screen.getByText("login")));
    await act(() => user.click(screen.getByText("logout")));

    expect(screen.getByTestId("email")).toHaveTextContent("none");
    expect(localStorage.getItem("arp.session")).toBeNull();
  });

  it("ignores an expired stored session", () => {
    localStorage.setItem(
      "arp.session",
      JSON.stringify({ token: "old", email: "old@b.com", expiresAt: Date.now() - 1000 }),
    );

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(screen.getByTestId("email")).toHaveTextContent("none");
  });
});
