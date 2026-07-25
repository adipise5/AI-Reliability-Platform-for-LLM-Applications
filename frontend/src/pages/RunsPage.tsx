import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listRuns } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function RunsPage() {
  const { session } = useAuth();
  const token = session!.token;

  const { data, isPending, error } = useQuery({
    queryKey: ["runs", token],
    queryFn: () => listRuns(token),
  });

  if (isPending) return <LoadingState label="Loading eval runs…" />;
  if (error) return <ErrorState error={error} />;

  return (
    <div className="page">
      <h1>Eval Runs</h1>
      {data.length === 0 ? (
        <p className="empty-state">No eval runs yet.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Status</th>
              <th>Score</th>
              <th>Dataset version</th>
              <th>Created</th>
              <th>Completed</th>
            </tr>
          </thead>
          <tbody>
            {data.map((run) => (
              <tr key={run.id}>
                <td>
                  <Link to={`/runs/${run.id}`}>{run.model}</Link>
                </td>
                <td>
                  <StatusBadge value={run.status} />
                </td>
                <td>{run.aggregate_score != null ? run.aggregate_score.toFixed(4) : "—"}</td>
                <td>{run.dataset_version ?? "—"}</td>
                <td>{new Date(run.created_at).toLocaleString()}</td>
                <td>{run.completed_at ? new Date(run.completed_at).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
