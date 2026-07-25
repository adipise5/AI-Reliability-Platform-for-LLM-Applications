import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getRunDetail } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { session } = useAuth();
  const token = session!.token;

  const { data, isPending, error } = useQuery({
    queryKey: ["run", runId, token],
    queryFn: () => getRunDetail(token, runId!),
    enabled: Boolean(runId),
  });

  if (isPending) return <LoadingState label="Loading run…" />;
  if (error) return <ErrorState error={error} />;

  const { run, items, gate_decision } = data;

  return (
    <div className="page">
      <p>
        <Link to="/runs">← Back to runs</Link>
      </p>
      <h1>{run.model}</h1>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Status</div>
          <div className="stat-value">
            <StatusBadge value={run.status} />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Aggregate score</div>
          <div className="stat-value">
            {run.aggregate_score != null ? run.aggregate_score.toFixed(4) : "—"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Prompt ID</div>
          <div className="stat-value stat-value--mono">{run.prompt_id}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Dataset version</div>
          <div className="stat-value">{run.dataset_version ?? "—"}</div>
        </div>
      </div>

      <section className="panel">
        <h2>Regression gate</h2>
        {gate_decision ? (
          <div className="gate-summary">
            <StatusBadge value={gate_decision.verdict} />
            <span>
              observed {gate_decision.observed_score.toFixed(4)} vs. baseline{" "}
              {gate_decision.baseline_mean.toFixed(4)} ± {gate_decision.baseline_stddev.toFixed(4)}
            </span>
          </div>
        ) : (
          <p className="empty-state">This run hasn't been gated yet.</p>
        )}
      </section>

      <section className="panel">
        <h2>Item results ({items.length})</h2>
        {items.length === 0 ? (
          <p className="empty-state">No item results.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Output</th>
                <th>Latency</th>
                <th>Scores</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="cell-output">{item.output}</td>
                  <td>{item.latency_ms.toFixed(0)}ms</td>
                  <td>
                    {item.scores.map((s) => (
                      <span key={s.scorer_name} className="score-chip">
                        {s.scorer_name}: {s.value.toFixed(2)}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
