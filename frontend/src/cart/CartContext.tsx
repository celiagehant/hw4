import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

/**
 * One cart line. Only the product ID, size and quantity are kept; name, price,
 * image and stock are always read fresh from the product API, so the cart never
 * holds a second copy of catalogue data.
 */
export interface CartItem {
  product_id: string;
  size: string | null; // null for products without sizes
  quantity: number;
}

interface CartState {
  items: CartItem[];
  /** Total number of units in the cart (shown in the navigation bar). */
  count: number;
  quantityOf: (productId: string, size: string | null) => number;
  /** Adds up to `quantity` units without exceeding `stock`; returns how many were added. */
  add: (productId: string, size: string | null, quantity: number, stock: number) => number;
  /** Sets a line's quantity, kept between 1 and `stock`. */
  setQuantity: (productId: string, size: string | null, quantity: number, stock: number) => void;
  remove: (productId: string, size: string | null) => void;
  clear: () => void;
}

// sessionStorage keeps the cart through navigation and page refreshes for the
// current browser session, for guests and logged-in customers alike.
const STORAGE_KEY = "campus-customs-cart-v1";

const CartContext = createContext<CartState | null>(null);

function isCartItem(value: unknown): value is CartItem {
  const v = value as CartItem;
  return (
    typeof v === "object" &&
    v !== null &&
    typeof v.product_id === "string" &&
    (v.size === null || typeof v.size === "string") &&
    Number.isInteger(v.quantity) &&
    v.quantity > 0
  );
}

function loadCart(): CartItem[] {
  try {
    const parsed: unknown = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter(isCartItem) : [];
  } catch {
    return [];
  }
}

const sameLine = (item: CartItem, productId: string, size: string | null) =>
  item.product_id === productId && item.size === size;

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(loadCart);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const quantityOf = (productId: string, size: string | null) =>
    items.find((item) => sameLine(item, productId, size))?.quantity ?? 0;

  function add(productId: string, size: string | null, quantity: number, stock: number): number {
    const current = quantityOf(productId, size);
    const added = Math.max(0, Math.min(quantity, stock - current));
    if (added === 0) return 0;
    setItems((prev) =>
      prev.some((item) => sameLine(item, productId, size))
        ? prev.map((item) => (sameLine(item, productId, size) ? { ...item, quantity: item.quantity + added } : item))
        : [...prev, { product_id: productId, size, quantity: added }],
    );
    return added;
  }

  function setQuantity(productId: string, size: string | null, quantity: number, stock: number) {
    const next = Math.max(1, Math.min(Math.floor(quantity), stock));
    setItems((prev) => prev.map((item) => (sameLine(item, productId, size) ? { ...item, quantity: next } : item)));
  }

  function remove(productId: string, size: string | null) {
    setItems((prev) => prev.filter((item) => !sameLine(item, productId, size)));
  }

  const count = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <CartContext.Provider
      value={{ items, count, quantityOf, add, setQuantity, remove, clear: () => setItems([]) }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartState {
  const context = useContext(CartContext);
  if (!context) throw new Error("useCart must be used inside CartProvider");
  return context;
}
