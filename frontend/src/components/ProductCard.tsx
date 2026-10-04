import { Link } from "react-router-dom";
import { formatPrice, formatSizes, type Availability } from "../api/products";
import { CardAddToCart } from "./AddToCart";

/** The fields a product card needs; both catalogue products and chat product matches provide them. */
export interface ProductCardData {
  product_id: string;
  name: string;
  price: number | null;
  image_url: string | null;
  description: string | null;
  garment_type?: string | null;
  availability?: Availability;
  sizes_in_stock?: string[];
  /** Why a recommended product fits the request (chat recommendations only). */
  match_reason?: string | null;
}

interface ProductCardProps {
  product: ProductCardData;
  /** Smaller layout used inside the chat panel. */
  compact?: boolean;
  /** Larger editorial layout for featured products. */
  featured?: boolean;
}

function stockBadge(availability?: Availability): { label: string; tone: string } | null {
  if (availability === "low_stock") return { label: "Low stock", tone: "accent" };
  if (availability === "out_of_stock") return { label: "Sold out", tone: "muted" };
  return null;
}

export default function ProductCard({ product, compact = false, featured = false }: ProductCardProps) {
  const href = `/products/${encodeURIComponent(product.product_id)}`;
  const badge = stockBadge(product.availability);
  const sizes = product.sizes_in_stock ?? [];
  const className = ["product-card", compact && "compact", featured && "featured"].filter(Boolean).join(" ");

  return (
    <article className={className}>
      <Link to={href} className="product-card-link">
        <div className="product-card-media">
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} loading="lazy" />
          ) : (
            <div className="product-card-no-image">No photo</div>
          )}
          {badge && <span className={`card-badge ${badge.tone}`}>{badge.label}</span>}
        </div>
        <div className="product-card-body">
          {product.garment_type && !compact && <p className="product-card-type">{product.garment_type}</p>}
          <h3>{product.name}</h3>
          <p className="price">{product.price === null ? "Price unavailable" : formatPrice(product.price)}</p>
          {product.description && <p className="short-description">{product.description}</p>}
          {!compact && sizes.length > 0 && (
            <p className="product-card-sizes">
              <span className="sr-only">Sizes in stock: </span>
              {formatSizes(sizes)}
            </p>
          )}
          {product.match_reason && (
            <p className="match-reason">
              <span className="match-reason-label">Why Dan picked it</span>
              {product.match_reason}
            </p>
          )}
        </div>
      </Link>
      <div className="product-card-actions">
        {compact && (
          <Link to={href} className="button ghost small">
            View Product
          </Link>
        )}
        <CardAddToCart productId={product.product_id} compact={compact} />
      </div>
    </article>
  );
}
