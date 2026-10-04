import { useState } from "react";
import { Link } from "react-router-dom";
import { fetchProduct, hasSizes, type ProductDetail, type StockLevel } from "../api/products";
import { useCart } from "../cart/CartContext";

function stockNote(quantity: number): string {
  if (quantity <= 0) return "Sold out";
  if (quantity <= 5) return `${quantity} left`;
  return "In stock";
}

/** Size buttons built from the product's inventory rows; sold-out sizes are disabled. */
function SizePicker({
  inventory,
  selected,
  onSelect,
  compact = false,
}: {
  inventory: StockLevel[];
  selected: string | null;
  onSelect: (size: string) => void;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "size-picker compact" : "size-picker"} role="group" aria-label="Choose a size">
      {inventory.map((row) => (
        <button
          key={row.size}
          type="button"
          className={row.size === selected ? "selected" : undefined}
          disabled={row.quantity <= 0}
          aria-pressed={row.size === selected}
          aria-label={`Size ${row.size}, ${stockNote(row.quantity)}`}
          onClick={() => onSelect(row.size)}
          title={stockNote(row.quantity)}
        >
          {row.size === selected && !compact && (
            <span className="size-check" aria-hidden="true">
              ✓
            </span>
          )}
          <strong>{row.size}</strong>
          {!compact && <span>{stockNote(row.quantity)}</span>}
        </button>
      ))}
    </div>
  );
}

/** Full Add to Cart panel for the product detail page: size, quantity and stock limits. */
export function AddToCartPanel({ product }: { product: ProductDetail }) {
  const cart = useCart();
  const sized = hasSizes(product.inventory);
  const [size, setSize] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState<string | null>(null);

  if (product.inventory.length === 0) {
    return <p className="cart-note">Stock information isn't available for this product, so it can't be added to the cart.</p>;
  }

  const line = sized ? product.inventory.find((row) => row.size === size) : product.inventory[0];
  const lineSize = sized ? size : null;
  const stock = line?.quantity ?? 0;
  const inCart = line ? cart.quantityOf(product.product_id, lineSize) : 0;
  const canAdd = Math.max(0, stock - inCart);
  const allSoldOut = product.inventory.every((row) => row.quantity <= 0);

  function chooseSize(next: string) {
    setSize(next);
    setQuantity(1);
    setMessage(null);
  }

  function handleAdd() {
    if (!line) return;
    const added = cart.add(product.product_id, lineSize, quantity, stock);
    const label = lineSize ? ` in size ${lineSize}` : "";
    setMessage(
      added > 0
        ? `Added ${added} to your cart${label}.`
        : `You already have all ${stock} available${label} in your cart.`,
    );
    setQuantity(1);
  }

  const stockLine = !line
    ? sized
      ? "Select a size to see availability."
      : null
    : stock <= 0
      ? `Sold out${lineSize ? ` in ${lineSize}` : ""}.`
      : stock <= 5
        ? `Only ${stock} left${lineSize ? ` in ${lineSize}` : ""}.`
        : `In stock${lineSize ? ` in ${lineSize}` : ""}: ${stock} available.`;

  return (
    <div className="add-to-cart">
      {sized && (
        <div className="add-to-cart-sizes">
          <div className="add-to-cart-label">
            <span>Size</span>
            <span className="muted">{size ? `Selected: ${size}` : "Choose one"}</span>
          </div>
          <SizePicker inventory={product.inventory} selected={size} onSelect={chooseSize} />
        </div>
      )}
      {stockLine && (
        <p key={stockLine} className={`stock-line${line && stock <= 5 ? " low" : ""}`} aria-live="polite">
          <span className="stock-dot" aria-hidden="true" />
          {stockLine}
        </p>
      )}
      {allSoldOut ? (
        <p className="cart-note">This product is sold out in every size.</p>
      ) : (
        <div className="add-to-cart-row">
          <div className="quantity-stepper" role="group" aria-label="Quantity">
            <button
              type="button"
              aria-label="Decrease quantity"
              onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              disabled={quantity <= 1}
            >
              −
            </button>
            <span key={quantity} className="quantity-value" aria-live="polite">
              {quantity}
            </span>
            <button
              type="button"
              aria-label="Increase quantity"
              onClick={() => setQuantity((q) => Math.min(canAdd, q + 1))}
              disabled={!line || quantity >= canAdd}
            >
              +
            </button>
          </div>
          <button type="button" className="button primary large add-to-cart-cta" onClick={handleAdd} disabled={!line || canAdd === 0}>
            {sized && !size ? "Select a size" : "Add to Cart"}
          </button>
        </div>
      )}
      {line && inCart > 0 && (
        <p className="cart-note">
          {inCart} already in your cart{lineSize ? ` (size ${lineSize})` : ""}; {canAdd} more available.
        </p>
      )}
      {message && (
        <p className="cart-message" role="status">
          {message} <Link to="/cart">View cart</Link>
        </p>
      )}
    </div>
  );
}

/**
 * Add to Cart for product cards. Stock is loaded only when the button is clicked,
 * so cards stay light and the stock is current. Sized products show size buttons.
 */
export function CardAddToCart({ productId, compact = false }: { productId: string; compact?: boolean }) {
  const cart = useCart();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "choosing" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  function addLine(detail: ProductDetail, size: string | null) {
    const row = size === null ? detail.inventory[0] : detail.inventory.find((r) => r.size === size);
    if (!row) return;
    const added = cart.add(detail.product_id, size, 1, row.quantity);
    const label = size ? ` (${size})` : "";
    setMessage(added ? `Added${label} ✓` : `Max in cart${label}`);
    setState("idle");
  }

  async function start() {
    setMessage(null);
    setState("loading");
    try {
      const detail = product ?? (await fetchProduct(productId));
      setProduct(detail);
      if (detail.inventory.length === 0 || detail.inventory.every((r) => r.quantity <= 0)) {
        setMessage(detail.inventory.length === 0 ? "Stock unavailable" : "Sold out");
        setState("idle");
      } else if (!hasSizes(detail.inventory)) {
        addLine(detail, null);
      } else {
        setState("choosing");
      }
    } catch {
      setState("error");
    }
  }

  if (state === "choosing" && product) {
    return (
      <div className="card-cart">
        <span className="card-cart-label">Choose a size:</span>
        <SizePicker inventory={product.inventory} selected={null} onSelect={(s) => addLine(product, s)} compact />
        <button type="button" className="link-button" onClick={() => setState("idle")}>
          Cancel
        </button>
      </div>
    );
  }

  return (
    <div className="card-cart">
      <button
        type="button"
        className={compact ? "button small" : "button small block"}
        onClick={() => void start()}
        disabled={state === "loading"}
      >
        {state === "loading" ? "Loading…" : "Add to Cart"}
      </button>
      {state === "error" && <span className="card-cart-message error">Couldn't load sizes</span>}
      {message && <span className="card-cart-message">{message}</span>}
    </div>
  );
}
