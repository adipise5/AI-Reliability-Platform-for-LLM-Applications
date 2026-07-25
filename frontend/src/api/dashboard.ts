import { request } from "./client";
import type {
  DashboardOverview,
  RemoteBaseline,
  RemoteBudgetStatus,
  RemoteCheckRun,
  RemoteChannel,
  RemoteEvalRun,
  RemoteLatencyAnomaly,
  RemoteNotification,
  RemoteReport,
  RemoteTraceSummary,
  RemoteUsageSummary,
  RunDetail,
} from "./types";

const DASHBOARD_URL = import.meta.env.VITE_DASHBOARD_URL;

export function getOverview(token: string): Promise<DashboardOverview> {
  return request(DASHBOARD_URL, "/api/v1/dashboard/overview", { token });
}

export function listRuns(token: string): Promise<RemoteEvalRun[]> {
  return request(DASHBOARD_URL, "/api/v1/runs", { token });
}

export function getRunDetail(token: string, runId: string): Promise<RunDetail> {
  return request(DASHBOARD_URL, `/api/v1/runs/${runId}`, { token });
}

export function getCostSummary(token: string): Promise<RemoteUsageSummary> {
  return request(DASHBOARD_URL, "/api/v1/cost/summary", { token });
}

export function getBudgetStatus(token: string): Promise<RemoteBudgetStatus> {
  return request(DASHBOARD_URL, "/api/v1/cost/budget", { token });
}

export function getBaseline(token: string, promptId: string): Promise<RemoteBaseline | null> {
  return request(DASHBOARD_URL, `/api/v1/regression/baselines/${promptId}`, { token });
}

export function getLatencyAnomaly(token: string): Promise<RemoteLatencyAnomaly> {
  return request(DASHBOARD_URL, "/api/v1/regression/latency-anomaly", { token });
}

export function listReports(token: string, experimentId?: string): Promise<RemoteReport[]> {
  return request(DASHBOARD_URL, "/api/v1/reports", { token, query: { experiment_id: experimentId } });
}

export function getReport(token: string, reportId: string): Promise<RemoteReport> {
  return request(DASHBOARD_URL, `/api/v1/reports/${reportId}`, { token });
}

export function listChannels(token: string): Promise<RemoteChannel[]> {
  return request(DASHBOARD_URL, "/api/v1/notifications/channels", { token });
}

export function listNotifications(token: string, channelId?: string): Promise<RemoteNotification[]> {
  return request(DASHBOARD_URL, "/api/v1/notifications", { token, query: { channel_id: channelId } });
}

export function listChecks(
  token: string,
  repo?: string,
  commitSha?: string,
): Promise<RemoteCheckRun[]> {
  return request(DASHBOARD_URL, "/api/v1/github/checks", {
    token,
    query: { repo, commit_sha: commitSha },
  });
}

export function listRecentTraces(token: string, limit = 20): Promise<RemoteTraceSummary[]> {
  return request(DASHBOARD_URL, "/api/v1/traces", { token, query: { limit } });
}

const REPORT_GENERATOR_URL = import.meta.env.VITE_REPORT_GENERATOR_URL;

// Report content (HTML/PDF bytes) isn't proxied through the Dashboard
// Backend — see its README — so this calls the Report Generator directly
// with the same bearer token, rather than going through api/client.ts's
// JSON-only `request` helper.
export async function downloadReportContent(token: string, reportId: string): Promise<Blob> {
  const response = await fetch(`${REPORT_GENERATOR_URL}/api/v1/reports/${reportId}/content`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`report content request failed (${response.status})`);
  return response.blob();
}
