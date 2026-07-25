import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as dashboardApi from "../api/dashboard";
import { AuthProvider } from "../auth/AuthContext";
import { OverviewPage } from "./OverviewPage";

vi.mock("../api/dashboard");

function renderOverview() {
  localStorage.setItem(
    "arp.session",
    JSON.stringify({ token: "tok", email: "a@b.com", expiresAt: Date.now() + 60_000 }),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AuthProvider>
          <OverviewPage />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("OverviewPage", () => {
  it("renders budget, cost, and recent runs once the overview loads", async () => {
    vi.mocked(dashboardApi.getOverview).mockResolvedValue({
      recent_runs: [
        {
          id: "11111111-1111-1111-1111-111111111111",
          prompt_id: "p1",
          prompt_version_id: "v1",
          dataset_id: "d1",
          dataset_version: 1,
          model: "claude-sonnet-5",
          status: "completed",
          aggregate_score: 0.9,
          created_at: "2026-01-01T00:00:00Z",
          completed_at: "2026-01-01T00:01:00Z",
        },
      ],
      cost_summary: {
        total_cost_usd: 42.0,
        total_prompt_tokens: 1000,
        total_completion_tokens: 500,
        by_model: [],
      },
      budget_status: {
        spent_this_month_usd: 12.5,
        limit_usd: 100,
        remaining_usd: 87.5,
        over_budget: false,
      },
      latency_anomaly: {
        sample_count: 10,
        recent_mean_ms: 120,
        baseline_mean_ms: 100,
        baseline_stddev_ms: 10,
        is_anomalous: false,
        insufficient_data: false,
      },
      recent_notifications: [],
    });

    renderOverview();

    expect(await screen.findByText("claude-sonnet-5")).toBeInTheDocument();
    expect(screen.getByText("$12.50")).toBeInTheDocument();
    expect(screen.getByText("$42.00")).toBeInTheDocument();
    expect(screen.getByText("No notifications sent yet.")).toBeInTheDocument();
  });

  it("shows an error state when the overview request fails", async () => {
    vi.mocked(dashboardApi.getOverview).mockRejectedValue(new Error("boom"));

    renderOverview();

    expect(await screen.findByText("Something went wrong.")).toBeInTheDocument();
  });
});
