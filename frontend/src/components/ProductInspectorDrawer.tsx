import React from "react";
import { formatMoney } from "../api";
import type { Product } from "../types";
import { useEscapeToClose } from "../useEscapeToClose";

interface ProductInspectorDrawerProps {
  product: Product | null;
  currency: string;
  isOpen: boolean;
  onClose: () => void;
  onReplace: (product: Product) => void;
  onOpenCatalog: (category: string) => void;
  userRole: "homeowner" | "designer";
}

export const ProductInspectorDrawer: React.FC<ProductInspectorDrawerProps> = ({
  product,
  currency,
  isOpen,
  onClose,
  onReplace,
  onOpenCatalog,
  userRole,
}) => {
  useEscapeToClose(isOpen, onClose);

  if (!isOpen || !product) return null;

  const widthIn = product.dimensions?.width_in;
  const depthIn = product.dimensions?.depth_in;
  const heightIn = product.dimensions?.height_in;

  const widthMm = widthIn ? Math.round(widthIn * 25.4) : null;
  const depthMm = depthIn ? Math.round(depthIn * 25.4) : null;
  const heightMm = heightIn ? Math.round(heightIn * 25.4) : null;

  const hasSmart = product.smart.features.length > 0;
  const isWatersense = product.water.watersense_eligible;

  return (
    <div className="inspector-drawer-backdrop" onClick={onClose}>
      <div
        className="inspector-drawer-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`Product details for ${product.name}`}
      >
        {/* Drawer Header */}
        <div className="inspector-header">
          <div className="inspector-category-badge">
            <span className="badge-luxury">{product.category.replace(/_/g, " ").toUpperCase()}</span>
            {product.tier && (
              <span className={`pill-tier tier-${product.tier}`}>{product.tier.toUpperCase()}</span>
            )}
          </div>
          <button
            type="button"
            className="btn-icon-close"
            onClick={onClose}
            aria-label="Close inspector"
          >
            ✕
          </button>
        </div>

        {/* Product Title & Family */}
        <div className="inspector-title-block">
          <h3 className="inspector-product-name">{product.name}</h3>
          {product.kohler_reference_family && (
            <p className="inspector-family-note">{product.kohler_reference_family}</p>
          )}
          <div className="inspector-price-row">
            <span className="inspector-price">
              {product.price !== null ? formatMoney(product.price, currency) : "Price on request"}
            </span>
            <span
              className="inspector-verified-badge"
              title={
                product.price_status === "illustrative"
                  ? "This price is a prototype placeholder, not a KOHLER quotation."
                  : "Price confirmed against a published source."
              }
            >
              {product.price_status === "illustrative"
                ? "≈ Illustrative price"
                : "✓ Confirmed price"}
            </span>
          </div>
        </div>

        {/* Product Visual Mockup / Rendering Block */}
        <div className="inspector-visual-card">
          <div className="visual-silhouette">
            <span className="visual-icon">
              {product.category === "toilet" || product.category === "smart_toilet"
                ? "🚽"
                : product.category === "shower" || product.category === "smart_shower"
                ? "🚿"
                : product.category === "vanity"
                ? "🪞"
                : product.category === "bathtub"
                ? "🛁"
                : "🚰"}
            </span>
            <span className="visual-label">{product.name}</span>
          </div>
        </div>

        {/* Technical & Installation Specifications */}
        <div className="inspector-section">
          <h4 className="inspector-section-title">
            {userRole === "designer" ? "ENGINEERING & ROUGH-IN SPECS" : "KEY DIMENSIONS & NEEDS"}
          </h4>

          <div className="inspector-specs-grid">
            {/* Dimensions */}
            <div className="spec-cell">
              <span className="spec-cell-label">DIMENSIONS</span>
              <span className="spec-cell-value">
                {widthIn}″W × {depthIn}″D{heightIn ? ` × ${heightIn}″H` : ""}
              </span>
              {userRole === "designer" && widthMm && (
                <span className="spec-cell-sub">
                  ({widthMm} × {depthMm}{heightMm ? ` × ${heightMm}` : ""} mm)
                </span>
              )}
            </div>

            {/* Electrical */}
            <div className="spec-cell">
              <span className="spec-cell-label">ELECTRICAL POWER</span>
              <span className="spec-cell-value">
                {product.electrical_required ? "120V GFCI Required" : "No Power Needed"}
              </span>
              <span className="spec-cell-sub">
                {product.electrical_required
                  ? userRole === "designer"
                    ? "Dedicated 15A branch circuit"
                    : "Standard wall outlet required"
                  : "Gravity / mechanical operation"}
              </span>
            </div>

            {/* Water Efficiency */}
            <div className="spec-cell">
              <span className="spec-cell-label">WATER CONSUMPTION</span>
              <span className="spec-cell-value">
                {product.water.flow_rate_gpm
                  ? `${product.water.flow_rate_gpm} GPM`
                  : product.water.flush_volume_gal
                  ? `${product.water.flush_volume_gal} GPF`
                  : "N/A (Dry Fixture)"}
              </span>
              <span className="spec-cell-sub">
                {isWatersense ? "💧 EPA WaterSense Eligible" : "Standard flow compliance"}
              </span>
            </div>

            {/* Smart Technology */}
            <div className="spec-cell">
              <span className="spec-cell-label">SMART CONNECTIVITY</span>
              <span className="spec-cell-value">
                {hasSmart ? "KOHLER Konnect™" : "Standard Manual"}
              </span>
              <span className="spec-cell-sub">
                {hasSmart
                  ? product.smart.features.join(", ")
                  : "No digital controls required"}
              </span>
            </div>
          </div>
        </div>

        {/* Verification Items / Human Explanations */}
        <div className="inspector-section">
          <h4 className="inspector-section-title">INSTALLATION &amp; FIELD VERIFICATION</h4>
          <div className="inspector-verification-card">
            {product.electrical_required && (
              <div className="verify-bullet">
                <span className="bullet-icon">⚡</span>
                <span className="bullet-text">
                  {userRole === "designer"
                    ? "Verify GFCI outlet position complies with wet-zone local code setback."
                    : "Make sure an electrician installs a safe outlet near this toilet."}
                </span>
              </div>
            )}
            <div className="verify-bullet">
              <span className="bullet-icon">📏</span>
              <span className="bullet-text">
                {userRole === "designer"
                  ? "Requires minimum 21″ front clear floor space per IRC R307.1."
                  : "Needs comfortable walkway in front so doors open smoothly."}
              </span>
            </div>
            <div className="verify-bullet">
              <span className="bullet-icon">🔧</span>
              <span className="bullet-text">
                {userRole === "designer"
                  ? "Standard plumbing wall rough-in inspection required prior to close-in."
                  : "Check that your wall plumbing matches this fixture before installing."}
              </span>
            </div>
          </div>
        </div>

        {/* Drawer Actions Footer */}
        <div className="inspector-footer">
          <button
            type="button"
            className="btn-replace-fixture"
            onClick={() => {
              onClose();
              onReplace(product);
            }}
          >
            <span>🔄</span> Swap with Alternative
          </button>
          <button
            type="button"
            className="btn-catalog-compare"
            onClick={() => {
              onClose();
              onOpenCatalog(product.category);
            }}
          >
            Browse in Catalog
          </button>
        </div>
      </div>
    </div>
  );
};
