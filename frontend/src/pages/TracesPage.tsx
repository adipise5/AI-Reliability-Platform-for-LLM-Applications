import { useQuery } from "@tanstack/react-query";
import { listRecentTraces } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function TracesPage() {
  const { session } = useAuth();
  const token = session!.token;

  const { data, isPending, error } = useQuery({
    queryKey: ["traces", token],
    queryFn: () => listRecentTraces(token, 50),
  });

  if (isPending) return <LoadingState label="Loading traces…" />;
  if (error) return <ErrorState error={error} />;

  return (
    <div className="page">
      <h1>Traces</h1>
      {data.length === 0 ? (
        <p className="empty-state">No traces recorded yet.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Trace ID</th>
              <th>Root span</th>
              <th>Spans</th>
              <th>Status</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {data.map((trace) => (
              <tr key={trace.trace_id}>
                <td className="stat-value--mono">{trace.trace_id.slice(0, 16)}</td>
                <td>{trace.root_span_name}</td>
                <td>{trace.span_count}</td>
                <td>
                  <StatusBadge value={trace.status} />
                </td>
                <td>{trace.duration_ms.toFixed(0)}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
