import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchProductFilters,
  fetchProducts,
  formatPrice,
  type ProductFilters,
  type ProductListItem,
} from "../api/products";
import ProductCard from "../components/ProductCard";
import DanAvatar from "../components/DanAvatar";
import { useChatUI } from "../chat/ChatUIContext";

/** Categories shown as tiles; broad umbrella categories ("sweatshirts", "shirts") are left out. */
const TILE_CATEGORIES = ["hoodies", "crewnecks", "quarter-zips", "t-shirts", "jackets"];
/** The featured collection: one product from each of these categories, chosen from live data. */
const FEATURED_CATEGORIES = ["hoodies", "crewnecks", "quarter-zips"];

const SUGGESTED_PROMPTS = [
  "Find me a Yale hoodie",
  "What's under $50?",
  "Help me find a gift",
  "Show me what's available in medium",
];

/** Best-stocked product per category (most sizes in stock, then name), so picks are always buyable. */
function bestInCategory(products: ProductListItem[], category: string, exclude: Set<string>) {
  return products
    .filter((p) => p.categories.includes(category) && !exclude.has(p.product_id))
    .sort((a, b) => b.sizes_in_stock.length - a.sizes_in_stock.length || a.name.localeCompare(b.name))[0];
}

export default function HomePage() {
  const chat = useChatUI();
  const [products, setProducts] = useState<ProductListItem[] | null>(null);
  const [filters, setFilters] = useState<ProductFilters | null>(null);

  useEffect(() => {
    fetchProducts({ in_stock: true })
      .then(setProducts)
      .catch(() => setProducts([]));
    fetchProductFilters()
      .then(setFilters)
      .catch(() => setFilters(null));
  }, []);

  const used = new Set<string>();
  const featured: ProductListItem[] = [];
  for (const category of FEATURED_CATEGORIES) {
    const pick = products && bestInCategory(products, category, used);
    if (pick) {
      featured.push(pick);
      used.add(pick.product_id);
    }
  }
  const heroImages = featured.slice(0, 3);

  const tiles = TILE_CATEGORIES.map((value) => {
    const meta = filters?.categories.find((c) => c.value === value);
    const inCategory = products?.filter((p) => p.categories.includes(value)) ?? [];
    const cover = inCategory[0];
    const from = inCategory.length ? Math.min(...inCategory.map((p) => p.price)) : null;
    return meta && cover ? { ...meta, cover, from } : null;
  }).filter((t): t is NonNullable<typeof t> => t !== null);

  const hoodieFrom = tiles.find((t) => t.value === "hoodies")?.from;

  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <div className="hero-inner container">
          <div className="hero-copy">
            <p className="eyebrow">Welcome to Campus Customs</p>
            <h1 className="hero-title">
              Your Yale.
              <br />
              <em>Your Style.</em>
            </h1>
            <p className="hero-lede">
              Official Yale University merchandise, from heritage crewnecks to game-day hoodies. Shop online or visit us
              at 57 Broadway.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="button primary large">
                Shop the Collection
              </Link>
              <button type="button" className="button secondary large with-avatar" onClick={chat.open}>
                <DanAvatar size={28} />
                Ask our AI stylist
              </button>
            </div>
          </div>

          <div className="hero-visual" aria-hidden={heroImages.length === 0}>
            {heroImages.map((p, i) => (
              <Link
                key={p.product_id}
                to={`/products/${encodeURIComponent(p.product_id)}`}
                className={`hero-frame hero-frame-${i + 1}`}
              >
                <img src={p.image_url} alt={p.name} />
              </Link>
            ))}
            {hoodieFrom != null && (
              <p className="hero-tag">
                Hoodies from <strong>{formatPrice(hoodieFrom)}</strong>
              </p>
            )}
          </div>
        </div>
      </section>

      <div className="trust-strip">
        <div className="container trust-inner">
          <span>Officially licensed Yale merchandise</span>
          {filters && filters.sizes.length > 0 && (
            <span>
              Sizes {filters.sizes[0]}–{filters.sizes[filters.sizes.length - 1]}, with live stock
            </span>
          )}
          <span>Visit us at 57 Broadway, New Haven</span>
        </div>
      </div>

      {/* Featured collection */}
      {featured.length > 0 && (
        <section className="section container">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Featured collection</p>
              <h2>Campus classics, ready to wear</h2>
            </div>
            <Link to="/products" className="text-link">
              Shop all products →
            </Link>
          </div>
          <div className="featured-grid">
            {featured.map((p, i) => (
              <ProductCard key={p.product_id} product={p} featured={i === 0} />
            ))}
          </div>
        </section>
      )}

      {/* Shop by category */}
      {tiles.length > 0 && (
        <section className="section section-tinted">
          <div className="container">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Shop by category</p>
                <h2>Find your fit</h2>
              </div>
            </div>
            <ul className="category-tiles">
              {tiles.map((t) => (
                <li key={t.value}>
                  <Link to={`/products?category=${encodeURIComponent(t.value)}`} className="category-tile">
                    <img src={t.cover.image_url} alt="" loading="lazy" />
                    <span className="category-tile-text">
                      <strong>{t.label}</strong>
                      <span>
                        {t.count} styles{t.from != null ? ` · from ${formatPrice(t.from)}` : ""}
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Meet Dan */}
      <section className="section container">
        <div className="dan-band">
          <DanAvatar size={88} />
          <div className="dan-band-copy">
            <p className="eyebrow">Your Yale shopping companion</p>
            <h2>Meet Dan</h2>
            <p>
              Named in the spirit of Handsome Dan, Yale's bulldog, Dan knows every item in the shop: prices, colors and
              which sizes are on the shelf right now. Ask for a gift idea, a budget pick or "this one in medium".
            </p>
            <div className="prompt-chips">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button key={prompt} type="button" className="prompt-chip" onClick={() => chat.ask(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
