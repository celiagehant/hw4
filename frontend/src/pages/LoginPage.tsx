import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { AuthError, logIn } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user && !submitting) return <Navigate to="/account" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setSubmitting(true);
    try {
      setUser(await logIn(email, password));
      navigate("/account", { replace: true });
    } catch (err) {
      setError(err instanceof AuthError ? err.message : "Could not reach the server. Please try again.");
      setPassword("");
      setSubmitting(false);
    }
  }

  return (
    <section className="content-card narrow">
      <h1>Log In</h1>
      {error && <p className="form-error">{error}</p>}
      <form className="form" onSubmit={handleSubmit} noValidate>
        <label>
          Email
          <input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button type="submit" className="button" disabled={submitting}>
          {submitting ? "Logging in…" : "Log In"}
        </button>
      </form>
      <p>
        New here? <Link to="/create-account">Create an account</Link>
      </p>
    </section>
  );
}
