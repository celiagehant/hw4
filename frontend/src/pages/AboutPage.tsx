import { Link } from "react-router-dom";

export default function AboutPage() {
  return (
    <section className="about">
      <header className="page-header">
        <p className="eyebrow">About Us</p>
        <h1>Everything you need to become a true Yalie</h1>
      </header>
      <div className="about-grid">
        <p className="about-text">
          We sell official licensed merchandise from Yale University, offering everything you need to become a true
          Yalie! If you are a student, staff, family member or just a visitor, we have you covered. You can visit us in
          our store at 57 Broadway, New Haven, CT 06511, or order online through our website.
        </p>
        <aside className="about-card">
          <h2>Visit the store</h2>
          <address>
            Campus Customs
            <br />
            57 Broadway
            <br />
            New Haven, CT 06511
          </address>
          <Link to="/products" className="button primary">
            Shop online
          </Link>
        </aside>
      </div>
    </section>
  );
}
