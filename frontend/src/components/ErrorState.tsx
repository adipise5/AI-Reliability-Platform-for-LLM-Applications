import { ApiError } from "../api/client";

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof ApiError ? error.message : "Something went wrong.";
  return <div className="error-state">{message}</div>;
}
