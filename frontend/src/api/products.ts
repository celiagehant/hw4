export interface StockLevel {
  size: string;
  quantity: number;
}

export type Availability = "in_stock" | "low_stock" | "out_of_stock" | "stock_unknown";

export interface Product {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  search_tags: string[];
  image_url: string;
  price: number;
}

/** A product as returned by GET /api/products: the catalogue row plus its stock. */
export interface ProductListItem extends Product {
  inventory: StockLevel[];
  sizes_in_stock: string[];
  availability: Availability;
  categories: string[];
}

export interface ProductDetail extends Product {
  inventory: StockLevel[];
}

export type SortOption = "recommended" | "name_asc" | "price_asc" | "price_desc";

/** Search, filter and sort parameters for GET /api/products. */
export interface ProductQuery {
  q?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  size?: string;
  in_stock?: boolean;
  sort?: SortOption;
}

/** Filter values from GET /api/products/filters, all derived from the database. */
export interface ProductFilters {
  categories: { value: string; label: string; count: number }[];
  sizes: string[];
  price: { min: number | null; max: number | null };
  availability: { in_stock: number; total: number };
  sort_options: { value: SortOption; label: string }[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(response.status === 404 ? "Product not found" : `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function fetchProducts(query: ProductQuery = {}, signal?: AbortSignal): Promise<ProductListItem[]> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === "" || value === false) continue;
    params.set(key, String(value));
  }
  const qs = params.toString();
  return getJson<ProductListItem[]>(`/api/products${qs ? `?${qs}` : ""}`, signal);
}

export function fetchProductFilters(): Promise<ProductFilters> {
  return getJson<ProductFilters>("/api/products/filters");
}

export function fetchProduct(productId: string, signal?: AbortSignal): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`, signal);
}

export function formatPrice(price: number): string {
  return price.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

/** Inventory labels that mean "one size" rather than a choice the customer must make. */
const ONE_SIZE_LABELS = new Set(["", "one size", "os", "o/s", "n/a", "na", "onesize"]);

/**
 * Whether the customer must pick a size: true unless the product's only inventory
 * row is a one-size row. Products with no inventory rows have no known stock.
 */
export function hasSizes(inventory: StockLevel[]): boolean {
  return !(inventory.length === 1 && ONE_SIZE_LABELS.has(inventory[0].size.trim().toLowerCase()));
}

const SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"];

/** "XS–XXL" when every size in between is present, otherwise a comma list. */
export function formatSizes(sizes: string[]): string {
  if (sizes.length === 0) return "";
  const idx = sizes.map((s) => SIZE_ORDER.indexOf(s));
  const consecutive = idx.every((v, i) => v >= 0 && (i === 0 || v === idx[i - 1] + 1));
  return sizes.length > 2 && consecutive ? `${sizes[0]}–${sizes[sizes.length - 1]}` : sizes.join(", ");
}
