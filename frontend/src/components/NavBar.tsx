import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useCart } from "../cart/CartContext";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/products", label: "Products", end: false },
  { to: "/about", label: "About Us", end: true },
];

function CartIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M5 8h14l-1.2 11.2a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8L5 8z" strokeLinejoin="round" />
      <path d="M9 8V6.5a3 3 0 0 1 6 0V8" strokeLinecap="round" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="12" cy="8.5" r="3.5" />
      <path d="M5 20c1.2-3.6 4-5.5 7-5.5s5.8 1.9 7 5.5" strokeLinecap="round" />
    </svg>
  );
}

export default function NavBar() {
  const { user, signOut } = useAuth();
  const { count } = useCart();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // The header slims down and gains a blurred background once the page scrolls.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close the mobile menu after navigating.
  useEffect(() => setMenuOpen(false), [location.pathname]);

  const cartLabel = `Cart, ${count} ${count === 1 ? "item" : "items"}`;

  return (
    <header className={`site-header${scrolled ? " scrolled" : ""}${menuOpen ? " menu-open" : ""}`}>
      <div className="utility-bar">
        <span>Official Yale University merchandise</span>
        <span className="utility-sep" aria-hidden="true">
          ·
        </span>
        <span>57 Broadway, New Haven</span>
      </div>
      <div className="header-inner">
        <Link to="/" className="wordmark" aria-label="Campus Customs, home">
          <span className="wordmark-mark" aria-hidden="true">
            CC
          </span>
          <span className="wordmark-text">
            <span className="wordmark-name">Campus Customs</span>
            <span className="wordmark-sub">Yale · New Haven</span>
          </span>
        </Link>

        <nav className="primary-nav" aria-label="Main">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="header-actions">
          {user ? (
            <div className="account-state">
              <NavLink to="/account" className="account-link">
                <UserIcon />
                <span>Hi, {user.first_name}</span>
              </NavLink>
              <button type="button" className="text-action" onClick={() => void signOut()}>
                Log Out
              </button>
            </div>
          ) : (
            <div className="account-state">
              <NavLink to="/login" className="account-link">
                <UserIcon />
                <span>Log In</span>
              </NavLink>
              <NavLink to="/create-account" className="text-action create-link">
                Create Account
              </NavLink>
            </div>
          )}
          <NavLink to="/cart" className="cart-link" aria-label={cartLabel}>
            <CartIcon />
            <span className="cart-link-label">Cart</span>
            <span key={count} className={`cart-badge${count > 0 ? " has-items" : ""}`} aria-hidden="true">
              {count}
            </span>
          </NavLink>
          <button
            type="button"
            className="menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span className="menu-toggle-bars" aria-hidden="true" />
            <span className="sr-only">{menuOpen ? "Close menu" : "Open menu"}</span>
          </button>
        </div>
      </div>

      <nav id="mobile-menu" className="mobile-menu" aria-label="Mobile" hidden={!menuOpen}>
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end}>
            {link.label}
          </NavLink>
        ))}
        <NavLink to="/cart">Cart ({count})</NavLink>
        {user ? (
          <>
            <NavLink to="/account">My account ({user.first_name})</NavLink>
            <button type="button" className="text-action" onClick={() => void signOut()}>
              Log Out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login">Log In</NavLink>
            <NavLink to="/create-account">Create Account</NavLink>
          </>
        )}
      </nav>
    </header>
  );
}
