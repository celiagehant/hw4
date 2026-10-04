import { Link } from "react-router-dom";
import { useChatUI } from "../chat/ChatUIContext";
import DanAvatar from "./DanAvatar";

export default function Footer() {
  const chat = useChatUI();
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <p className="footer-wordmark">Campus Customs</p>
          <p>Official licensed Yale University merchandise, for students, staff, families and visitors.</p>
        </div>
        <div>
          <h2>Shop</h2>
          <ul>
            <li>
              <Link to="/products">All products</Link>
            </li>
            <li>
              <Link to="/products?category=hoodies">Hoodies</Link>
            </li>
            <li>
              <Link to="/products?category=crewnecks">Crewnecks</Link>
            </li>
            <li>
              <Link to="/products?category=t-shirts">T-shirts</Link>
            </li>
          </ul>
        </div>
        <div>
          <h2>Visit</h2>
          <address>
            57 Broadway
            <br />
            New Haven, CT 06511
          </address>
          <Link to="/about">About us</Link>
        </div>
        <div>
          <h2>Need help?</h2>
          <button type="button" className="footer-dan" onClick={chat.open}>
            <DanAvatar size={32} />
            <span>Ask Dan, our shopping companion</span>
          </button>
        </div>
      </div>
      <p className="footer-legal">© Campus Customs · Official Yale University merchandise</p>
    </footer>
  );
}
