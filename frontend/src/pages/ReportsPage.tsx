import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { downloadReportContent, listReports } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import type { RemoteReport } from "../api/types";

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function ReportsPage() {
  const { session } = useAuth();
  const token = session!.token;
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const { data, isPending, error } = useQuery({
    queryKey: ["reports", token],
    queryFn: () => listReports(token),
  });

  async function handleDownload(report: RemoteReport) {
    setDownloadError(null);
    setDownloadingId(report.id);
    try {
      const blob = await downloadReportContent(token, report.id);
      triggerDownload(blob, `report-${report.id}.${report.format}`);
    } catch {
      setDownloadError("Could not download this report's content.");
    } finally {
      setDownloadingId(null);
    }
  }

  if (isPending) return <LoadingState label="Loading reports…" />;
  if (error) return <ErrorState error={error} />;

  return (
    <div className="page">
      <h1>Reports</h1>
      {downloadError && <p className="error-state">{downloadError}</p>}
      {data.length === 0 ? (
        <p className="empty-state">No reports have been requested yet.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Format</th>
              <th>Status</th>
              <th>Created</th>
              <th>Completed</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.map((report) => (
              <tr key={report.id}>
                <td>{report.format.toUpperCase()}</td>
                <td>
                  <StatusBadge value={report.status} />
                  {report.error_message && <div className="error-inline">{report.error_message}</div>}
                </td>
                <td>{new Date(report.created_at).toLocaleString()}</td>
                <td>{report.completed_at ? new Date(report.completed_at).toLocaleString() : "—"}</td>
                <td>
                  {report.status === "ready" && (
                    <button
                      type="button"
                      onClick={() => handleDownload(report)}
                      disabled={downloadingId === report.id}
                    >
                      {downloadingId === report.id ? "Downloading…" : "Download"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
