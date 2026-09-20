import React, { useEffect, useState } from "react";
import { api, formatMoney } from "../api";
import type { Product } from "../types";
import { useEscapeToClose } from "../useEscapeToClose";

interface CatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialCategory?: string | null;
  onSwapProduct?: (product: Product) => void;
  hasActivePlan: boolean;
}

export const CatalogModal: React.FC<CatalogModalProps> = ({
  isOpen,
  onClose,
  initialCategory,
  onSwapProduct,
  hasActivePlan,
}) => {
  useEscapeToClose(isOpen, onClose);

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedTier, setSelectedTier] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [disclaimer, setDisclaimer] = useState<string>("");

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);

    api
      .getCatalog()
      .then((res) => {
        setProducts(res.products);
        setCategories(res.categories);
        setDisclaimer(res.data_disclaimer);
        if (initialCategory && res.categories.includes(initialCategory)) {
          setSelectedCategory(initialCategory);
        }
      })
      .catch((err) => setError(err.message || "Failed to load product catalog"))
      .finally(() => setLoading(false));
  }, [isOpen, initialCategory]);

  if (!isOpen) return null;

  // Filter products
  const filteredProducts = products.filter((p) => {
    if (selectedCategory !== "all" && p.category !== selectedCategory) return false;
    if (selectedTier !== "all" && p.tier !== selectedTier) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = p.name.toLowerCase().includes(q);
      const matchFam = (p.kohler_reference_family || "").toLowerCase().includes(q);
      const matchCat = p.category.toLowerCase().includes(q);
      if (!matchName && !matchFam && !matchCat) return false;
    }
    return true;
  });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card catalog-modal-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="KOHLER Product Catalog Browser"
        style={{ maxWidth: "980px", width: "95vw" }}
      >
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <span className="badge-luxury">VERIFIED PRODUCT SPECIFICATION</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              KOHLER Product Catalog Explorer
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <p style={{ margin: "10px 0 14px", fontSize: "13px", color: "var(--ink-600)" }}>
          Browse the prototype catalog of sanitaryware, tapware, and furniture. Footprint dimensions,
          clearance envelopes, electrical requirements, and flow ratings drive every layout and
          feasibility check. Products are modelled on KOHLER product classes; prices are illustrative
          placeholders, not KOHLER quotations.
        </p>

        {/* Search & Category Filter Toolbar */}
        <div className="catalog-toolbar">
          <div className="catalog-search-wrap">
            <input
              type="search"
              className="catalog-search-input"
              placeholder="Search fixtures by name or type (e.g. vanity, wall-hung, thermostatic)…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="catalog-filters-row">
            {/* Category Filter */}
            <select
              className="catalog-filter-select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              aria-label="Filter by category"
            >
              <option value="all">All Categories ({products.length})</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, " ").toUpperCase()}
                </option>
              ))}
            </select>

            {/* Tier Filter */}
            <select
              className="catalog-filter-select"
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              aria-label="Filter by tier"
            >
              <option value="all">All Tiers</option>
              <option value="essential">Essential</option>
              <option value="standard">Standard</option>
              <option value="premium">Premium</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>
        </div>

        {error && <div className="callout callout-danger" style={{ margin: "12px 0" }}>{error}</div>}

        {/* Product Cards Grid */}
        {loading ? (
          <div style={{ padding: "50px 0", textAlign: "center", color: "var(--ink-500)" }}>
            Loading catalog fixtures…
          </div>
        ) : (
          <div className="catalog-cards-scrollable">
            {filteredProducts.length === 0 ? (
              <div className="catalog-empty-results">
                <p>No products match your search criteria.</p>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => {
                    setSelectedCategory("all");
                    setSelectedTier("all");
                    setSearchQuery("");
                  }}
                >
                  Reset Filters
                </button>
              </div>
            ) : (
              <div className="catalog-grid">
                {filteredProducts.map((p) => {
                  const widthIn = p.dimensions?.width_in;
                  const depthIn = p.dimensions?.depth_in;
                  const heightIn = p.dimensions?.height_in;

                  return (
                    <div key={p.id} className="catalog-product-card">
                      <div className="catalog-card-head">
                        <span className="catalog-cat-tag">{p.category.replace(/_/g, " ")}</span>
                        {p.tier && (
                          <span className={`pill-tier tier-${p.tier}`}>{p.tier}</span>
                        )}
                      </div>

                      <h4 className="catalog-card-title">{p.name}</h4>
                      {p.kohler_reference_family && (
                        <span className="catalog-card-family">{p.kohler_reference_family}</span>
                      )}

                      <div className="catalog-card-specs">
                        <div className="card-spec-dim">
                          <span>
                            {widthIn ? `${widthIn}″W` : "—"} × {depthIn ? `${depthIn}″D` : "—"}
                            {heightIn ? ` × ${heightIn}″H` : ""}
                          </span>
                        </div>
                        <div className="card-spec-badges">
                          {p.water.watersense_eligible && (
                            <span className="spec-pill pill-eco" title="WaterSense">
                              💧 Eco
                            </span>
                          )}
                          {p.electrical_required && (
                            <span className="spec-pill pill-electric" title="120V GFCI required">
                              ⚡ GFCI
                            </span>
                          )}
                          {p.smart.features.length > 0 && (
                            <span className="spec-pill pill-smart" title="Smart features">
                              Konnect
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="catalog-card-footer">
                        <span className="catalog-card-price">
                          {p.price !== null ? formatMoney(p.price, p.currency) : "Spec pricing"}
                        </span>

                        {hasActivePlan && onSwapProduct && (
                          <button
                            type="button"
                            className="btn-swap-product"
                            onClick={() => {
                              onSwapProduct(p);
                              onClose();
                            }}
                            title="Evaluate impact of swapping this fixture via DesignPulse"
                          >
                            Swap into Design
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Disclaimer Note */}
        {disclaimer && (
          <p className="catalog-disclaimer-note">
            <strong>Disclaimer:</strong> {disclaimer}
          </p>
        )}
      </div>
    </div>
  );
};
