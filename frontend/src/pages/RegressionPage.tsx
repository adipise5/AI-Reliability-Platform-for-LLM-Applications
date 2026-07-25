import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { getBaseline, getLatencyAnomaly } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatCard } from "../components/StatCard";

export function RegressionPage() {
  const { session } = useAuth();
  const token = session!.token;
  const [promptIdInput, setPromptIdInput] = useState("");
  const [promptId, setPromptId] = useState<string | null>(null);

  const anomalyQuery = useQuery({
    queryKey: ["latency-anomaly", token],
    queryFn: () => getLatencyAnomaly(token),
  });

  const baselineQuery = useQuery({
    queryKey: ["baseline", promptId, token],
    queryFn: () => getBaseline(token, promptId!),
    enabled: Boolean(promptId),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setPromptId(promptIdInput.trim() || null);
  }

  return (
    <div className="page">
      <h1>Regression</h1>

      <section className="panel">
        <h2>Gateway latency</h2>
        {anomalyQuery.isPending && <LoadingState />}
        {anomalyQuery.error && <ErrorState error={anomalyQuery.error} />}
        {anomalyQuery.data && (
          <div className="stat-grid">
            <StatCard
              label="Status"
              value={
                anomalyQuery.data.insufficient_data
                  ? "not enough data"
                  : anomalyQuery.data.is_anomalous
                    ? "anomalous"
                    : "normal"
              }
              tone={anomalyQuery.data.is_anomalous ? "warning" : "default"}
            />
            <StatCard
              label="Recent mean"
              value={
                anomalyQuery.data.recent_mean_ms != null
                  ? `${anomalyQuery.data.recent_mean_ms.toFixed(0)}ms`
                  : "—"
              }
            />
            <StatCard
              label="Baseline mean"
              value={
                anomalyQuery.data.baseline_mean_ms != null
                  ? `${anomalyQuery.data.baseline_mean_ms.toFixed(0)}ms`
                  : "—"
              }
            />
            <StatCard label="Samples" value={String(anomalyQuery.data.sample_count)} />
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Prompt baseline</h2>
        <p className="panel-hint">
          Look up a prompt's gate baseline by id — there's no prompt-browsing view yet (see the
          Dashboard Backend's README for why), but any prompt id from a run above works here.
        </p>
        <form className="inline-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Prompt ID"
            value={promptIdInput}
            onChange={(e) => setPromptIdInput(e.target.value)}
          />
          <button type="submit">Look up</button>
        </form>

        {baselineQuery.isPending && promptId && <LoadingState />}
        {baselineQuery.error && <ErrorState error={baselineQuery.error} />}
        {promptId && baselineQuery.data === null && (
          <p className="empty-state">This prompt has never been gated.</p>
        )}
        {baselineQuery.data && (
          <div className="stat-grid">
            <StatCard label="Mean score" value={baselineQuery.data.mean_score.toFixed(4)} />
            <StatCard label="Std. deviation" value={baselineQuery.data.stddev_score.toFixed(4)} />
            <StatCard label="Sample size" value={String(baselineQuery.data.sample_size)} />
          </div>
        )}
      </section>
    </div>
  );
}
