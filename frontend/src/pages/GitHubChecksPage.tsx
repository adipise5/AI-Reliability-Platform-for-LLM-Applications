import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { listChecks } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function GitHubChecksPage() {
  const { session } = useAuth();
  const token = session!.token;
  const [repoInput, setRepoInput] = useState("");
  const [repo, setRepo] = useState<string | undefined>(undefined);

  const { data, isPending, error } = useQuery({
    queryKey: ["checks", repo, token],
    queryFn: () => listChecks(token, repo),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setRepo(repoInput.trim() || undefined);
  }

  return (
    <div className="page">
      <h1>GitHub Checks</h1>

      <form className="inline-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="owner/repo (optional filter)"
          value={repoInput}
          onChange={(e) => setRepoInput(e.target.value)}
        />
        <button type="submit">Filter</button>
      </form>

      {isPending && <LoadingState label="Loading checks…" />}
      {error && <ErrorState error={error} />}
      {data &&
        (data.length === 0 ? (
          <p className="empty-state">No check runs yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Repo</th>
                <th>Commit</th>
                <th>Status</th>
                <th>Conclusion</th>
              </tr>
            </thead>
            <tbody>
              {data.map((check) => (
                <tr key={check.id}>
                  <td>{check.repo}</td>
                  <td className="stat-value--mono">{check.commit_sha.slice(0, 10)}</td>
                  <td>
                    <StatusBadge value={check.status} />
                  </td>
                  <td>
                    <StatusBadge value={check.conclusion} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}
    </div>
  );
}
