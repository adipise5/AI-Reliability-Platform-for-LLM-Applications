import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getOverview } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";

export function OverviewPage() {
  const { session } = useAuth();
  const token = session!.token;

  const { data, isPending, error } = useQuery({
    queryKey: ["overview", token],
    queryFn: () => getOverview(token),
  });

  if (isPending) return <LoadingState label="Loading dashboard…" />;
  if (error) return <ErrorState error={error} />;

  const { cost_summary, budget_status, latency_anomaly, recent_runs, recent_notifications } = data;

  return (
    <div className="page">
      <h1>Overview</h1>

      <div className="stat-grid">
        <StatCard
          label="Spend this month"
          value={budget_status ? `$${budget_status.spent_this_month_usd.toFixed(2)}` : "—"}
          hint={
            budget_status?.limit_usd != null
              ? `of $${budget_status.limit_usd.toFixed(2)} budget`
              : "no budget set"
          }
          tone={budget_status?.over_budget ? "danger" : "default"}
        />
        <StatCard
          label="Total cost (all time)"
          value={cost_summary ? `$${cost_summary.total_cost_usd.toFixed(2)}` : "—"}
          hint={cost_summary ? `${cost_summary.by_model.length} model(s)` : undefined}
        />
        <StatCard
          label="Gateway latency"
          value={
            latency_anomaly?.insufficient_data
              ? "not enough data"
              : latency_anomaly?.is_anomalous
                ? "anomalous"
                : "normal"
          }
          tone={latency_anomaly?.is_anomalous ? "warning" : "default"}
          hint={
            latency_anomaly?.recent_mean_ms != null
              ? `${latency_anomaly.recent_mean_ms.toFixed(0)}ms recent avg`
              : undefined
          }
        />
        <StatCard label="Recent runs" value={String(recent_runs.length)} />
      </div>

      <section className="panel">
        <h2>Recent eval runs</h2>
        {recent_runs.length === 0 ? (
          <p className="empty-state">No eval runs yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Status</th>
                <th>Score</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {recent_runs.map((run) => (
                <tr key={run.id}>
                  <td>
                    <Link to={`/runs/${run.id}`}>{run.model}</Link>
                  </td>
                  <td>
                    <StatusBadge value={run.status} />
                  </td>
                  <td>{run.aggregate_score != null ? run.aggregate_score.toFixed(4) : "—"}</td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h2>Recent notifications</h2>
        {recent_notifications.length === 0 ? (
          <p className="empty-state">No notifications sent yet.</p>
        ) : (
          <ul className="list">
            {recent_notifications.map((n) => (
              <li key={n.id}>
                <StatusBadge value={n.status} />
                <span>{n.subject}</span>
                <span className="list-timestamp">{new Date(n.created_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
