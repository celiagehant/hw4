import { Link, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function AccountPage() {
  const { user, loading, signOut } = useAuth();
  const location = useLocation();
  const welcome = (location.state as { welcome?: boolean } | null)?.welcome;

  if (loading) return <p>Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <section className="content-card narrow">
      <h1>{welcome ? `Welcome, ${user.first_name}!` : `Hi, ${user.first_name}!`}</h1>
      <p className="form-success">
        {welcome ? "Your account was created and you are logged in." : "You are logged in."}
      </p>
      <dl className="product-facts">
        <dt>Name</dt>
        <dd>
          {user.first_name} {user.last_name}
        </dd>
        <dt>Email</dt>
        <dd className="no-transform">{user.email}</dd>
      </dl>
      <p>
        <Link to="/products" className="button">
          Browse Products
        </Link>{" "}
        <button type="button" className="button secondary" onClick={() => void signOut()}>
          Log Out
        </button>
      </p>
    </section>
  );
}
