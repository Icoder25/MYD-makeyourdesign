import React from "react";
import { formatLitres, formatMoney } from "../api";
import type { CandidatePlan, DesignState, Product } from "../types";

const CATEGORY_ORDER = [
  "vanity",
  "basin",
  "faucet",
  "toilet",
  "smart_toilet",
  "shower",
  "smart_shower",
  "bathtub",
  "storage",
  "mirror",
];

interface ProductSpecificationSheetProps {
  state: DesignState | null;
  candidate: CandidatePlan | null;
  onOpenInspiration: () => void;
  onOpenCatalog?: (category?: string) => void;
  onHoverProduct?: (productId: string | null) => void;
  onSelectProduct?: (product: Product) => void;
  userRole?: "homeowner" | "designer";
}

export const ProductSpecificationSheet: React.FC<ProductSpecificationSheetProps> = ({
  state,
  candidate,
  onOpenInspiration,
  onOpenCatalog,
  onHoverProduct,
  onSelectProduct,
  userRole = "homeowner",
}) => {
  if (!state || !state.selected_products) {
    return (
      <div className="product-sheet-empty">
        <div className="empty-icon">📦</div>
        <h3>No Products Selected</h3>
        <p>Active specifications will appear here once a plan is generated.</p>
      </div>
    );
  }

  const products = state.selected_products;
  const currency = state.currency || "INR";
  const totalPrice = state.total_price;
  const budgetLimit = state.budget_limit;
  const remainingBudget = state.remaining_budget;
  const water = state.water_impact || candidate?.water_impact;

  // Sort products by standard architectural schedule order
  const sortedProducts = [...products].sort((a, b) => {
    const idxA = CATEGORY_ORDER.indexOf(a.category);
    const idxB = CATEGORY_ORDER.indexOf(b.category);
    return (idxA >= 0 ? idxA : 99) - (idxB >= 0 ? idxB : 99);
  });

  return (
    <section className="studio-column product-spec-column">
      {/* Column Header */}
      <div className="column-card-header">
        <div className="header-title-row">
          <span className="column-label">COLUMN 2 · PRODUCTS IN THIS DESIGN</span>
          <span className="spec-count-pill">{products.length} Fixtures</span>
        </div>
        <h2 className="column-title">Selected KOHLER Fixtures</h2>
        <p className="column-subtext">
          {userRole === "designer"
            ? "Click any fixture line item to inspect rough-in tolerances, electrical GFCI specs, or swap alternatives."
            : "Click any fixture to see how it fits your bathroom and swap options."}
        </p>
      </div>

      {/* Financial & Environmental Investment Header Card */}
      <div className="investment-summary-card">
        <div className="invest-metric">
          <span className="invest-label">TOTAL INVESTMENT</span>
          <span className="invest-value">{formatMoney(totalPrice, currency)}</span>
          {budgetLimit !== null && (
            <span className="invest-sub">
              Cap: {formatMoney(budgetLimit, currency)} (
              {remainingBudget !== null && remainingBudget >= 0
                ? `${formatMoney(remainingBudget, currency)} under`
                : `${formatMoney(Math.abs(remainingBudget ?? 0), currency)} over`}
              )
            </span>
          )}
        </div>

        {water && water.status === "calculated" && water.annual_litres_saved !== null && (
          <div className="invest-metric water-metric">
            <span className="invest-label">WATER CONSERVATION</span>
            <span className="invest-value text-green">
              {formatLitres(water.annual_litres_saved)}/yr
            </span>
            <span className="invest-sub">
              {water.percent_saved
                ? `${water.percent_saved.toFixed(0)}% below standard baseline`
                : "WaterSense compliant"}
            </span>
          </div>
        )}
      </div>

      {/* Fixture Schedule Line Items */}
      <div className="spec-items-scrollable">
        <ul className="spec-item-list" role="list">
          {sortedProducts.map((product: Product) => {
            const widthIn = product.dimensions?.width_in;
            const depthIn = product.dimensions?.depth_in;
            const heightIn = product.dimensions?.height_in;

            return (
              <li
                key={product.id}
                className="spec-item-row"
                onMouseEnter={() => onHoverProduct && onHoverProduct(product.id)}
                onMouseLeave={() => onHoverProduct && onHoverProduct(null)}
                onClick={() => onSelectProduct && onSelectProduct(product)}
                role="button"
                tabIndex={0}
                aria-label={`Inspect ${product.name}`}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    onSelectProduct && onSelectProduct(product);
                  }
                }}
              >
                <div className="spec-item-header">
                  <div className="spec-item-category">
                    <span className="category-tag">{product.category.replace(/_/g, " ")}</span>
                    {product.kohler_reference_family && (
                      <span className="family-tag">{product.kohler_reference_family}</span>
                    )}
                  </div>
                  <span className="spec-item-price">
                    {product.price !== null ? formatMoney(product.price, currency) : "Quoted on spec"}
                  </span>
                </div>

                <div className="spec-item-title-row">
                  <span className="spec-product-name">{product.name}</span>
                  <span className="spec-inspect-hint">Details ›</span>
                </div>

                <div className="spec-item-tech-row">
                  <div className="spec-dimension-box">
                    <span>
                      {widthIn ? `${widthIn}″W` : "—"} × {depthIn ? `${depthIn}″D` : "—"}
                      {heightIn ? ` × ${heightIn}″H` : ""}
                    </span>
                    {userRole === "designer" && widthIn && depthIn && (
                      <span className="spec-dim-mm">
                        ({Math.round(widthIn * 25.4)} × {Math.round(depthIn * 25.4)} mm)
                      </span>
                    )}
                  </div>

                  <div className="spec-badges">
                    {product.tier && <span className="spec-pill pill-tier">{product.tier}</span>}
                    {product.water.watersense_eligible && (
                      <span className="spec-pill pill-eco" title="WaterSense eligible">
                        💧 Eco
                      </span>
                    )}
                    {product.smart.features.length > 0 && (
                      <span className="spec-pill pill-smart">⚡ Smart</span>
                    )}
                    {product.electrical_required && (
                      <span className="spec-pill pill-electric">🔌 120V</span>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Bottom Actions Bar */}
      <div className="spec-footer-bar">
        {onOpenCatalog && (
          <button
            type="button"
            className="btn-open-catalog-spec"
            onClick={() => onOpenCatalog()}
          >
            <span>📦</span> Browse KOHLER Catalog
          </button>
        )}
        <button
          type="button"
          className="btn-curate-palette"
          onClick={onOpenInspiration}
        >
          <span>✨</span> Curate Style &amp; Materials
        </button>
      </div>
    </section>
  );
};
