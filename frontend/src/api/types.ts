// Mirrors of the Dashboard Backend's and Auth service's Pydantic response
// schemas. Field names are kept exactly as the JSON wire format (snake_case)
// rather than mapped to camelCase — there's no transform layer, so what you
// see here is what the network tab shows.

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterOrgResponse {
  org_id: string;
  org_name: string;
  owner_id: string;
  owner_email: string;
}

export interface ApiErrorBody {
  type: string;
  message: string;
}

export interface RemoteEvalRun {
  id: string;
  prompt_id: string;
  prompt_version_id: string;
  dataset_id: string;
  dataset_version: number | null;
  model: string;
  status: string;
  aggregate_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface RemoteScore {
  scorer_name: string;
  value: number;
}

export interface RemoteRunItemResult {
  id: string;
  dataset_item_id: string;
  output: string;
  latency_ms: number;
  scores: RemoteScore[];
}

export interface RemoteGateDecision {
  run_id: string;
  verdict: "pass" | "fail" | "needs_review" | string;
  observed_score: number;
  baseline_mean: number;
  baseline_stddev: number;
}

export interface RunDetail {
  run: RemoteEvalRun;
  items: RemoteRunItemResult[];
  gate_decision: RemoteGateDecision | null;
}

export interface RemoteModelUsage {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
}

export interface RemoteUsageSummary {
  total_cost_usd: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  by_model: RemoteModelUsage[];
}

export interface RemoteBudgetStatus {
  spent_this_month_usd: number;
  limit_usd: number | null;
  remaining_usd: number | null;
  over_budget: boolean;
}

export interface RemoteBaseline {
  prompt_id: string;
  mean_score: number;
  stddev_score: number;
  sample_size: number;
}

export interface RemoteLatencyAnomaly {
  sample_count: number;
  recent_mean_ms: number | null;
  baseline_mean_ms: number | null;
  baseline_stddev_ms: number | null;
  is_anomalous: boolean;
  insufficient_data: boolean;
}

export interface RemoteReport {
  id: string;
  experiment_id: string;
  format: "html" | "pdf" | string;
  status: "pending" | "generating" | "ready" | "failed" | string;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface RemoteChannel {
  id: string;
  channel_type: "slack" | "email" | "webhook" | string;
  name: string;
  target: string;
  enabled: boolean;
}

export interface RemoteNotification {
  id: string;
  channel_id: string;
  subject: string;
  status: "pending" | "sent" | "failed" | string;
  created_at: string;
}

export interface RemoteCheckRun {
  id: string;
  repo: string;
  commit_sha: string;
  status: "queued" | "completed" | string;
  conclusion: "success" | "failure" | "neutral" | null;
  run_id: string | null;
}

export interface RemoteTraceSummary {
  trace_id: string;
  root_span_name: string;
  span_count: number;
  status: string;
  duration_ms: number;
}

export interface DashboardOverview {
  recent_runs: RemoteEvalRun[];
  cost_summary: RemoteUsageSummary | null;
  budget_status: RemoteBudgetStatus | null;
  latency_anomaly: RemoteLatencyAnomaly | null;
  recent_notifications: RemoteNotification[];
}
