import { useQuery } from "@tanstack/react-query";
import { getBudgetStatus, getCostSummary } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatCard } from "../components/StatCard";

export function CostPage() {
  const { session } = useAuth();
  const token = session!.token;

  const summaryQuery = useQuery({ queryKey: ["cost-summary", token], queryFn: () => getCostSummary(token) });
  const budgetQuery = useQuery({ queryKey: ["budget-status", token], queryFn: () => getBudgetStatus(token) });

  if (summaryQuery.isPending || budgetQuery.isPending) return <LoadingState label="Loading cost data…" />;
  if (summaryQuery.error) return <ErrorState error={summaryQuery.error} />;
  if (budgetQuery.error) return <ErrorState error={budgetQuery.error} />;

  const summary = summaryQuery.data;
  const budget = budgetQuery.data;

  return (
    <div className="page">
      <h1>Cost & Budget</h1>

      <div className="stat-grid">
        <StatCard label="Total cost" value={`$${summary.total_cost_usd.toFixed(2)}`} />
        <StatCard label="Prompt tokens" value={summary.total_prompt_tokens.toLocaleString()} />
        <StatCard label="Completion tokens" value={summary.total_completion_tokens.toLocaleString()} />
        <StatCard
          label="Spent this month"
          value={`$${budget.spent_this_month_usd.toFixed(2)}`}
          hint={budget.limit_usd != null ? `of $${budget.limit_usd.toFixed(2)} limit` : "no limit set"}
          tone={budget.over_budget ? "danger" : "default"}
        />
      </div>

      <section className="panel">
        <h2>Usage by model</h2>
        {summary.by_model.length === 0 ? (
          <p className="empty-state">No usage recorded yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Provider</th>
                <th>Model</th>
                <th>Prompt tokens</th>
                <th>Completion tokens</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {summary.by_model.map((m) => (
                <tr key={`${m.provider}-${m.model}`}>
                  <td>{m.provider}</td>
                  <td>{m.model}</td>
                  <td>{m.prompt_tokens.toLocaleString()}</td>
                  <td>{m.completion_tokens.toLocaleString()}</td>
                  <td>${m.cost_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
