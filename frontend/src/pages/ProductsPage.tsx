import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import {
  fetchProductFilters,
  fetchProducts,
  formatPrice,
  type ProductFilters,
  type ProductListItem,
  type SortOption,
} from "../api/products";

const SEARCH_DELAY_MS = 350;
const FILTER_KEYS = ["q", "category", "min_price", "max_price", "size", "in_stock", "sort"];

/** Waits until `value` has stopped changing for `delay` ms, so typing doesn't send a request per key. */
function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

const toNumber = (value: string | null) => (value && !Number.isNaN(Number(value)) ? Number(value) : undefined);

export default function ProductsPage() {
  // All search/filter/sort state lives in the URL, so it survives refresh and the back button.
  const [params, setParams] = useSearchParams();
  const [filters, setFilters] = useState<ProductFilters | null>(null);
  const [products, setProducts] = useState<ProductListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Text inputs update the URL only after the customer pauses typing.
  const [searchText, setSearchText] = useState(params.get("q") ?? "");
  const [minText, setMinText] = useState(params.get("min_price") ?? "");
  const [maxText, setMaxText] = useState(params.get("max_price") ?? "");
  const debouncedSearch = useDebounced(searchText, SEARCH_DELAY_MS);
  const debouncedMin = useDebounced(minText, SEARCH_DELAY_MS);
  const debouncedMax = useDebounced(maxText, SEARCH_DELAY_MS);

  function update(changes: Record<string, string | null>) {
    // Start from the URL as it is right now, not from the last render's copy:
    // two filter changes in quick succession (e.g. a debounced price, then a
    // category) would otherwise overwrite each other.
    const next = new URLSearchParams(window.location.search);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null || value === "") next.delete(key);
      else next.set(key, value);
    }
    setParams(next, { replace: true });
  }

  useEffect(() => {
    if ((params.get("q") ?? "") !== debouncedSearch.trim()) update({ q: debouncedSearch.trim() });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);
  useEffect(() => {
    if ((params.get("min_price") ?? "") !== debouncedMin) update({ min_price: debouncedMin });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedMin]);
  useEffect(() => {
    if ((params.get("max_price") ?? "") !== debouncedMax) update({ max_price: debouncedMax });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedMax]);

  useEffect(() => {
    fetchProductFilters()
      .then(setFilters)
      .catch(() => setFilters(null));
  }, []);

  const query = {
    q: params.get("q") ?? undefined,
    category: params.get("category") ?? undefined,
    min_price: toNumber(params.get("min_price")),
    max_price: toNumber(params.get("max_price")),
    size: params.get("size") ?? undefined,
    in_stock: params.get("in_stock") === "true",
    sort: (params.get("sort") as SortOption | null) ?? "recommended",
  };
  const queryKey = params.toString();

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    fetchProducts(query, controller.signal)
      .then(setProducts)
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refetch when the URL's filters change
  }, [queryKey]);

  const active = FILTER_KEYS.some((key) => key !== "sort" && params.get(key));
  const priceInvalid =
    query.min_price !== undefined && query.max_price !== undefined && query.min_price > query.max_price;

  function clearAll() {
    setSearchText("");
    setMinText("");
    setMaxText("");
    setParams(new URLSearchParams(), { replace: true });
  }

  return (
    <section>
      <header className="page-header">
        <p className="eyebrow">Products</p>
        <h1>Shop the Collection</h1>
        <p className="page-lede">
          Every piece of official Yale merchandise we carry, with live stock. Search, filter by category, size or price,
          and sort to find yours.
        </p>
      </header>

      <div className="product-toolbar">
        <input
          type="search"
          className="product-search"
          placeholder="Search by name, type or description…"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          aria-label="Search products"
        />
        <div className="product-filters">
          <label>
            Category
            <select value={query.category ?? ""} onChange={(e) => update({ category: e.target.value })}>
              <option value="">All categories</option>
              {filters?.categories.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label} ({c.count})
                </option>
              ))}
            </select>
          </label>
          <label>
            Size in stock
            <select value={query.size ?? ""} onChange={(e) => update({ size: e.target.value })}>
              <option value="">Any size</option>
              {filters?.sizes.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Min price
            <input
              type="number"
              min={0}
              inputMode="decimal"
              placeholder={filters?.price.min != null ? formatPrice(filters.price.min) : "Min"}
              value={minText}
              onChange={(e) => setMinText(e.target.value)}
            />
          </label>
          <label>
            Max price
            <input
              type="number"
              min={0}
              inputMode="decimal"
              placeholder={filters?.price.max != null ? formatPrice(filters.price.max) : "Max"}
              value={maxText}
              onChange={(e) => setMaxText(e.target.value)}
            />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={query.in_stock}
              onChange={(e) => update({ in_stock: e.target.checked ? "true" : null })}
            />
            In stock only
            {filters && <span className="muted"> ({filters.availability.in_stock})</span>}
          </label>
          <label>
            Sort by
            <select
              value={query.sort}
              onChange={(e) => update({ sort: e.target.value === "recommended" ? null : e.target.value })}
            >
              {(filters?.sort_options ?? [{ value: "recommended", label: "Recommended" }]).map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="product-toolbar-status">
          <span>
            {products ? `${products.length} ${products.length === 1 ? "product" : "products"}` : "Loading…"}
            {priceInvalid && <span className="error"> · Min price is higher than max price</span>}
          </span>
          {(active || query.sort !== "recommended") && (
            <button type="button" className="link-button" onClick={clearAll}>
              Clear all filters
            </button>
          )}
        </div>
      </div>

      {error && <p className="error">Could not load products: {error}</p>}
      {products && products.length === 0 && (
        <div className="content-card empty-state">
          <h2>No products match your search</h2>
          <p className="muted">
            Try different words, choose another category or size, widen the price range, or turn off "In stock only".
          </p>
          <button type="button" className="button" onClick={clearAll}>
            Clear all filters
          </button>
        </div>
      )}
      {products && products.length > 0 && (
        <div className="product-grid">
          {products.map((product) => (
            <ProductCard key={product.product_id} product={product} />
          ))}
        </div>
      )}
    </section>
  );
}
