import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerOrg } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "./AuthContext";

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [orgName, setOrgName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await registerOrg(orgName, email, password);
      // Registration doesn't return a session token — log in right after
      // with the same credentials so the flow feels like one step.
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the auth service.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create your organization</h1>
        <p className="auth-subtitle">One admin account, created for you as the owner</p>

        <label htmlFor="orgName">Organization name</label>
        <input
          id="orgName"
          type="text"
          value={orgName}
          onChange={(e) => setOrgName(e.target.value)}
          required
          autoFocus
        />

        <label htmlFor="email">Owner email</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label htmlFor="password">Owner password</label>
        <input
          id="password"
          type="password"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <p className="auth-error">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Creating…" : "Create organization"}
        </button>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
