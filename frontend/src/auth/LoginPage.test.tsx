import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as authApi from "../api/auth";
import { ApiError } from "../api/client";
import { AuthProvider } from "./AuthContext";
import { LoginPage } from "./LoginPage";

vi.mock("../api/auth");

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<div>dashboard home</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("LoginPage", () => {
  it("navigates to the dashboard after a successful login", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: "tok",
      token_type: "bearer",
      expires_in: 3600,
    });
    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(screen.getByText("dashboard home")).toBeInTheDocument());
  });

  it("shows the server's error message on invalid credentials", async () => {
    vi.mocked(authApi.login).mockRejectedValue(
      new ApiError(401, { type: "invalid_credentials", message: "Invalid email or password." }),
    );
    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
  });
});
