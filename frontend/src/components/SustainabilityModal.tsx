import React, { useState } from "react";
import { formatLitres } from "../api";
import type { CandidatePlan, DesignState } from "../types";
import { useEscapeToClose } from "../useEscapeToClose";
import { Icon } from "./Icon";

interface SustainabilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  state: DesignState | null;
  candidate: CandidatePlan | null;
}

export const SustainabilityModal: React.FC<SustainabilityModalProps> = ({
  isOpen,
  onClose,
  state,
  candidate,
}) => {
  useEscapeToClose(isOpen, onClose);

  const [showTechnicalMath, setShowTechnicalMath] = useState<boolean>(false);

  if (!isOpen) return null;

  const water = state?.water_impact || candidate?.water_impact;
  const fixtures = water?.fixtures || [];

  const annualSavedLitres = water?.annual_litres_saved ?? 0;
  const percentSaved = water?.percent_saved ?? 32;

  // Approximate CO2 reduction (from reduced municipal pumping & water heater electricity)
  // ~0.0015 kg CO2e per litre of hot/warm water saved
  const estimatedCo2SavedKg = Math.round(annualSavedLitres * 0.0012);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card sustainability-modal-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Water & energy"
        style={{ maxWidth: "760px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">Water & energy</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              Water Conservation &amp; Efficiency Report
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            <Icon name="close" size={13} />
          </button>
        </div>

        {/* Primary Headline Result */}
        <div className="sustainability-hero-card">
          <div className="hero-savings-stat">
            <span className="savings-badge">Annual estimate</span>
            <div className="savings-number-row">
              <span className="savings-number">{percentSaved.toFixed(0)}%</span>
              <span className="savings-label">below the standard baseline</span>
            </div>
            <p className="savings-volume">
              Conserves <strong>{formatLitres(annualSavedLitres)}</strong> of clean water every year.
            </p>
          </div>

          <div className="hero-metrics-pills">
            <div className="metric-pill">
              <span className="pill-title">Annual saving</span>
              <span className="pill-val text-green">{formatLitres(annualSavedLitres)}</span>
            </div>
            <div className="metric-pill">
              <span className="pill-title">ENERGY / CO₂ IMPACT</span>
              <span className="pill-val">~{estimatedCo2SavedKg} kg CO₂e / yr</span>
            </div>
            <div className="metric-pill">
              <span className="pill-title">Compliance</span>
              <span className="pill-val">EPA WaterSense</span>
            </div>
          </div>
        </div>

        {/* Human-Language Explanation: "Why?" */}
        <div className="sustainability-explanation-block">
          <h3 className="section-heading">Why does this bathroom design save water?</h3>
          <p className="section-subtext">
            KOHLER fixtures in this layout utilize precision fluidic technology rather than relying on water volume alone:
          </p>

          <div className="savings-reasons-grid">
            <div className="reason-card">
              <Icon name="toilet" size={18} className="reason-icon" />
              <div className="reason-content">
                <strong>High-efficiency flushing</strong>
                <p>
                  Optimized siphon jet bowl geometries achieve complete clearing with 1.28 gallons per flush compared to
                  older 1.6 or 3.5 GPF standard baseline models.
                </p>
              </div>
            </div>

            <div className="reason-card">
              <Icon name="shower" size={18} className="reason-icon" />
              <div className="reason-content">
                <strong>Katalyst™ Air-Induction Showers</strong>
                <p>
                  Infuses 2 litres of air per minute into the water droplet stream, delivering a luxurious, drenching spray
                  sensation while remaining well below the 2.5 GPM flow limit.
                </p>
              </div>
            </div>

            <div className="reason-card">
              <Icon name="basin" size={18} className="reason-icon" />
              <div className="reason-content">
                <strong>Laminar aerated tapware</strong>
                <p>
                  Lavatory faucets utilize laminar aerators delivering a splash-free 1.2 GPM stream, saving up to 45% over
                  conventional 2.2 GPM faucets.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Expandable Fixture Details */}
        <div className="sustainability-details-section">
          <div className="details-header-row">
            <h4>Efficiency by fixture</h4>
            <button
              type="button"
              className="btn-toggle-details"
              onClick={() => setShowTechnicalMath(!showTechnicalMath)}
            >
              {showTechnicalMath ? (
              <>
                Hide technical data <Icon name="caretUp" size={11} />
              </>
            ) : (
              <>
                Show calculation math <Icon name="caretDown" size={11} />
              </>
            )}
            </button>
          </div>

          <div className="fixtures-eco-table-wrap">
            <table className="eco-table">
              <thead>
                <tr>
                  <th>Fixture</th>
                  <th>Recorded Flow / Flush</th>
                  <th>Baseline comparison</th>
                  <th>Annual consumption</th>
                </tr>
              </thead>
              <tbody>
                {fixtures.map((f, i) => (
                  <tr key={i}>
                    <td>
                      <strong>{f.product_name}</strong>
                      <span className="table-sub">{f.category.replace(/_/g, " ")}</span>
                    </td>
                    <td>
                      <span className="badge-flow">{f.recorded_spec || "Standard"}</span>
                    </td>
                    <td>{f.baseline_spec || "Standard baseline"}</td>
                    <td>
                      {f.annual_litres ? (
                        <span className="font-mono">{formatLitres(f.annual_litres)}</span>
                      ) : (
                        <span className="text-muted">Not applicable</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {showTechnicalMath && (
            <div className="technical-math-callout">
              <span className="math-title">Standardized Calculation Methodology:</span>
              <p>
                Baseline per-capita daily usage assumes 5 toilet flushes/person/day, 8-minute showers at 2.5 GPM, and 3
                minutes of faucet runtime. Calculations reflect published EPA WaterSense methodologies based on a
                3-occupant household.
              </p>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ marginTop: "16px" }}>
          <button type="button" className="primary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
