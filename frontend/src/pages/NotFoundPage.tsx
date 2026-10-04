import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section className="content-card">
      <h1>Page not found</h1>
      <p>
        <Link to="/">Go back home</Link>
      </p>
    </section>
  );
}
