import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProduct, formatPrice, type ProductDetail } from "../api/products";
import { useCart, type CartItem } from "../cart/CartContext";

type Loaded = Record<string, ProductDetail | "missing">;

function stockFor(product: ProductDetail, item: CartItem): number {
  const row = item.size === null ? product.inventory[0] : product.inventory.find((r) => r.size === item.size);
  return row?.quantity ?? 0;
}

export default function CartPage() {
  const cart = useCart();
  const [products, setProducts] = useState<Loaded>({});
  const [error, setError] = useState<string | null>(null);
  const [notices, setNotices] = useState<string[]>([]);

  // Name, image, price and stock always come from the product API, never from the cart.
  const ids = [...new Set(cart.items.map((item) => item.product_id))].sort().join(",");
  useEffect(() => {
    if (!ids) return;
    const controller = new AbortController();
    Promise.all(
      ids.split(",").map((id) =>
        fetchProduct(id, controller.signal).then(
          (p) => [id, p] as const,
          (err: Error) => {
            if (err.name === "AbortError") throw err;
            return [id, "missing"] as const;
          },
        ),
      ),
    )
      .then((entries) => {
        setProducts(Object.fromEntries(entries));
        setError(null);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError("Could not load your cart. Please try again.");
      });
    return () => controller.abort();
  }, [ids]);

  // If stock dropped below what's in the cart (or the product is gone), fix the cart and say so.
  useEffect(() => {
    const changes: string[] = [];
    for (const item of cart.items) {
      const product = products[item.product_id];
      if (product === undefined) continue;
      const label = item.size ? ` (size ${item.size})` : "";
      if (product === "missing") {
        cart.remove(item.product_id, item.size);
        changes.push(`An item${label} is no longer in our catalogue and was removed.`);
        continue;
      }
      const stock = stockFor(product, item);
      if (stock <= 0) {
        cart.remove(item.product_id, item.size);
        changes.push(`${product.name}${label} is now sold out and was removed.`);
      } else if (item.quantity > stock) {
        cart.setQuantity(item.product_id, item.size, stock, stock);
        changes.push(`Only ${stock} of ${product.name}${label} left, so your quantity was reduced.`);
      }
    }
    if (changes.length) setNotices((prev) => [...prev, ...changes]);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-check whenever fresh product data arrives
  }, [products]);

  if (cart.items.length === 0) {
    return (
      <section className="content-card cart-empty">
        <h1>Your cart is empty</h1>
        {notices.map((n) => (
          <p key={n} className="cart-note">
            {n}
          </p>
        ))}
        <p className="muted">Find something you love and add it to your cart.</p>
        <Link to="/products" className="button">
          Browse Products
        </Link>
      </section>
    );
  }

  // Notices describe automatic corrections; once the customer edits the cart they are stale.
  const userEdit = (change: () => void) => {
    setNotices([]);
    change();
  };

  const loading = cart.items.some((item) => products[item.product_id] === undefined);
  const total = cart.items.reduce((sum, item) => {
    const product = products[item.product_id];
    return product && product !== "missing" ? sum + product.price * item.quantity : sum;
  }, 0);

  return (
    <section>
      <h1>Your Cart</h1>
      {error && <p className="error">{error}</p>}
      {notices.map((n) => (
        <p key={n} className="cart-message">
          {n}
        </p>
      ))}
      <div className="cart-layout">
        <ul className="cart-lines">
          {cart.items.map((item) => {
            const product = products[item.product_id];
            const key = `${item.product_id}|${item.size ?? ""}`;
            if (!product || product === "missing") {
              return (
                <li key={key} className="cart-line">
                  Loading…
                </li>
              );
            }
            const stock = stockFor(product, item);
            const link = `/products/${encodeURIComponent(product.product_id)}`;
            return (
              <li key={key} className="cart-line">
                <Link to={link}>
                  <img src={product.image_url} alt={product.name} />
                </Link>
                <div className="cart-line-info">
                  <Link to={link} className="cart-line-name">
                    {product.name}
                  </Link>
                  {item.size && <span>Size: {item.size}</span>}
                  <span>Unit price: {formatPrice(product.price)}</span>
                  {item.quantity >= stock && <span className="cart-note">Max available: {stock}</span>}
                </div>
                <div className="quantity-stepper" aria-label={`Quantity of ${product.name}`}>
                  <button
                    type="button"
                    onClick={() => userEdit(() => cart.setQuantity(item.product_id, item.size, item.quantity - 1, stock))}
                    disabled={item.quantity <= 1}
                    aria-label="Decrease quantity"
                  >
                    −
                  </button>
                  <span aria-live="polite">{item.quantity}</span>
                  <button
                    type="button"
                    onClick={() => userEdit(() => cart.setQuantity(item.product_id, item.size, item.quantity + 1, stock))}
                    disabled={item.quantity >= stock}
                    aria-label="Increase quantity"
                  >
                    +
                  </button>
                </div>
                <strong className="cart-line-total">{formatPrice(product.price * item.quantity)}</strong>
                <button type="button" className="link-button" onClick={() => userEdit(() => cart.remove(item.product_id, item.size))}>
                  Remove
                </button>
              </li>
            );
          })}
        </ul>
        <aside className="cart-summary">
          <h2>Order summary</h2>
          <p>
            <span>Items</span>
            <span>{cart.count}</span>
          </p>
          <p className="cart-total">
            <span>Total</span>
            <span>{loading ? "…" : formatPrice(total)}</span>
          </p>
          <button type="button" className="button block" disabled>
            Checkout
          </button>
          <p className="muted small">Online checkout isn't available yet.</p>
          <button type="button" className="link-button" onClick={() => userEdit(cart.clear)}>
            Empty cart
          </button>
        </aside>
      </div>
    </section>
  );
}
