import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "./AuthContext";
import { RequireAuth } from "./RequireAuth";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>login page</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div>protected home</div>} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("RequireAuth", () => {
  it("redirects to /login when there is no session", () => {
    renderAt("/");

    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("renders the protected route when a valid session exists", () => {
    localStorage.setItem(
      "arp.session",
      JSON.stringify({ token: "tok", email: "a@b.com", expiresAt: Date.now() + 60_000 }),
    );

    renderAt("/");

    expect(screen.getByText("protected home")).toBeInTheDocument();

    localStorage.clear();
  });
});
