import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct, formatPrice, formatSizes, type ProductDetail } from "../api/products";
import { AddToCartPanel } from "../components/AddToCart";
import DanAvatar from "../components/DanAvatar";
import { useChatUI } from "../chat/ChatUIContext";

export default function ProductDetailPage() {
  const { productId = "" } = useParams();
  const chat = useChatUI();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setProduct(null);
    setError(null);
    fetchProduct(productId)
      .then(setProduct)
      .catch((err: Error) => setError(err.message));
  }, [productId]);

  if (error) {
    return (
      <section className="container narrow-page">
        <p className="error">{error}</p>
        <Link to="/products" className="back-link">
          ← Back to all products
        </Link>
      </section>
    );
  }
  if (!product) {
    return (
      <section className="container product-detail skeleton" aria-busy="true">
        <div className="product-gallery" />
        <div className="product-info">
          <p className="muted">Loading product…</p>
        </div>
      </section>
    );
  }

  const inStock = product.inventory.filter((row) => row.quantity > 0).map((row) => row.size);

  return (
    <div className="container">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/products">Products</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{product.name}</span>
      </nav>

      <section className="product-detail">
        <div className="product-gallery">
          <div className="product-gallery-frame">
            <img src={product.image_url} alt={product.name} />
          </div>
        </div>

        <div className="product-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1 className="product-title">{product.name}</h1>
          <p className="product-price">{formatPrice(product.price)}</p>
          <p className="product-description">{product.description}</p>

          {product.colors.length > 0 && (
            <div className="product-colors">
              <span className="product-colors-label">Colors</span>
              <ul>
                {product.colors.map((color) => (
                  <li key={color}>{color}</li>
                ))}
              </ul>
            </div>
          )}

          <AddToCartPanel key={product.product_id} product={product} />

          <button type="button" className="ask-dan" onClick={chat.open}>
            <DanAvatar size={36} />
            <span>
              <strong>Questions about this {product.garment_type ? "piece" : "product"}?</strong>
              <span>Ask Dan about sizes, colors or similar styles.</span>
            </span>
          </button>

          <dl className="product-facts">
            <div>
              <dt>Type</dt>
              <dd>{product.garment_type}</dd>
            </div>
            <div>
              <dt>Colors</dt>
              <dd>{product.colors.join(", ")}</dd>
            </div>
            <div>
              <dt>Sizes in stock</dt>
              <dd>{inStock.length ? formatSizes(inStock) : "Currently sold out"}</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
