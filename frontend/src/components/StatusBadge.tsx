const POSITIVE = new Set(["pass", "success", "sent", "completed", "ready", "ok"]);
const NEGATIVE = new Set(["fail", "failure", "failed", "error"]);
const NEUTRAL_WARN = new Set(["needs_review", "neutral", "pending", "queued", "generating", "running"]);

function toneFor(value: string): "positive" | "negative" | "warning" | "neutral" {
  const normalized = value.toLowerCase();
  if (POSITIVE.has(normalized)) return "positive";
  if (NEGATIVE.has(normalized)) return "negative";
  if (NEUTRAL_WARN.has(normalized)) return "warning";
  return "neutral";
}

export function StatusBadge({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="badge badge--neutral">—</span>;
  return <span className={`badge badge--${toneFor(value)}`}>{value.replace(/_/g, " ")}</span>;
}
