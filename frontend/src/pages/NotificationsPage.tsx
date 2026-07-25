import { useQuery } from "@tanstack/react-query";
import { listChannels, listNotifications } from "../api/dashboard";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";

export function NotificationsPage() {
  const { session } = useAuth();
  const token = session!.token;

  const channelsQuery = useQuery({ queryKey: ["channels", token], queryFn: () => listChannels(token) });
  const notificationsQuery = useQuery({
    queryKey: ["notifications", token],
    queryFn: () => listNotifications(token),
  });

  return (
    <div className="page">
      <h1>Notifications</h1>

      <section className="panel">
        <h2>Channels</h2>
        {channelsQuery.isPending && <LoadingState />}
        {channelsQuery.error && <ErrorState error={channelsQuery.error} />}
        {channelsQuery.data &&
          (channelsQuery.data.length === 0 ? (
            <p className="empty-state">No channels configured yet.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Target</th>
                  <th>Enabled</th>
                </tr>
              </thead>
              <tbody>
                {channelsQuery.data.map((c) => (
                  <tr key={c.id}>
                    <td>{c.name}</td>
                    <td>{c.channel_type}</td>
                    <td className="cell-output">{c.target}</td>
                    <td>{c.enabled ? "yes" : "no"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ))}
      </section>

      <section className="panel">
        <h2>Sent notifications</h2>
        {notificationsQuery.isPending && <LoadingState />}
        {notificationsQuery.error && <ErrorState error={notificationsQuery.error} />}
        {notificationsQuery.data &&
          (notificationsQuery.data.length === 0 ? (
            <p className="empty-state">No notifications sent yet.</p>
          ) : (
            <ul className="list">
              {notificationsQuery.data.map((n) => (
                <li key={n.id}>
                  <StatusBadge value={n.status} />
                  <span>{n.subject}</span>
                  <span className="list-timestamp">{new Date(n.created_at).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          ))}
      </section>
    </div>
  );
}
