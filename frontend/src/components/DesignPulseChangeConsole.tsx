import { useState } from "react";
import { formatMoney } from "../api";
import { Icon } from "./Icon";
import type {
  DesignState,
  ImpactReport,
  TradeoffOption,
} from "../types";

const SUGGESTIONS = [
  "Make vanity 60 inches.",
  "Upgrade to smart toilet.",
  "Add a bathtub.",
  "Shift to water-saving fixtures.",
  "Increase vanity storage.",
];

interface Props {
  activeState: DesignState;
  impactReport: ImpactReport | null;
  onAnalyze: (message: string) => void;
  onApplyTradeoff: (tradeoff: TradeoffOption) => void;
  onKeepCurrent?: () => void;
  onCompareVersions?: () => void;
  busy: boolean;
  llmAvailable: boolean;
  userRole?: "homeowner" | "designer";
}

export function DesignPulseChangeConsole({
  activeState,
  impactReport,
  onAnalyze,
  onApplyTradeoff,
  onKeepCurrent,
  onCompareVersions,
  busy,
  llmAvailable,
  userRole = "homeowner",
}: Props) {
  const [message, setMessage] = useState("");
  const [selectedTradeoffId, setSelectedTradeoffId] = useState<string | null>(null);

  const handleSubmit = (text: string) => {
    if (!text.trim() || busy) return;
    onAnalyze(text.trim());
    setSelectedTradeoffId(null);
  };

  const currentVanity = activeState.selected_products.find(
    (p) => p.category === "vanity"
  );
  const currentVanityWidth = currentVanity?.dimensions?.width_in;

  return (
    <section className="studio-column copilot-column">
      {/* Header */}
      <div className="column-card-header">
        <div className="header-title-row">
          <span className="column-label">Consequences</span>
          <span className="copilot-brand-pill">DesignPulse™</span>
        </div>
        <h2 className="column-title">Change one thing, see what it moves</h2>
        <p className="column-subtext">
          {userRole === "designer"
            ? "Deterministic dependency graph traverses clearances, rough-in constraints, and pricing in real time."
            : "Request any layout change. See exactly what changes, what stays the same, and what it costs."}
        </p>
      </div>

      <div className="copilot-body-scrollable">
        {/* Change Request Input Box */}
        <div className="copilot-input-card">
          <label className="copilot-input-label" htmlFor="designpulse-input">
            What would you like to adjust?
          </label>
          <form
            className="copilot-form"
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit(message);
            }}
          >
            <div className="input-with-button">
              <input
                id="designpulse-input"
                className="copilot-text-input"
                value={message}
                placeholder="e.g. Make vanity 60 inches."
                onChange={(e) => setMessage(e.target.value)}
                disabled={busy}
              />
              <button
                type="submit"
                className="btn-copilot-submit"
                disabled={busy || !message.trim()}
              >
                {busy ? "Evaluating…" : "Evaluate"}
              </button>
            </div>
          </form>

          {/* Quick Intent Chips */}
          <div className="copilot-chips-row">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="copilot-chip"
                disabled={busy}
                onClick={() => {
                  setMessage(suggestion);
                  handleSubmit(suggestion);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>

          {!llmAvailable && (
            <div className="copilot-engine-note">
              <span>Deterministic intent solver active · Instant constraint evaluation</span>
            </div>
          )}
        </div>

        {/* Impact Analysis & Consequence Results */}
        {impactReport ? (
          <div className="copilot-impact-results">
            {/* 1. Change Detection Banner */}
            <div className="change-detection-card">
              <div className="detection-header">
                <span className="detection-badge">Change understood as</span>
                <span className="detection-category">
                  {impactReport.changed_category.toUpperCase()}
                </span>
              </div>
              <div className="detection-spec-transition">
                <div className="transition-item prev-item">
                  <span className="item-role">Current Baseline:</span>
                  <span className="item-name">
                    {impactReport.previous_product.name} (
                    {impactReport.previous_product.dimensions?.width_in ?? currentVanityWidth}&quot;)
                  </span>
                </div>
                <span className="transition-arrow">→</span>
                <div className="transition-item new-item">
                  <span className="item-role">Proposed Target:</span>
                  <span className="item-name">
                    {impactReport.new_product.name} (
                    {impactReport.new_product.dimensions?.width_in ??
                      (impactReport.previous_product.dimensions?.width_in ?? 0) +
                        (impactReport.dimensional_delta.width_in ?? 0)}
                    &quot;)
                  </span>
                </div>
              </div>
            </div>

            {/* 2. Structured Impact Breakdown (Affected vs Unchanged) */}
            <div className="impact-consequences-grid">
              <div className="consequence-box affected-box">
                <span className="box-title">Affected by this change</span>
                <div className="badge-wrap">
                  {impactReport.affected_categories.map((cat) => (
                    <span key={cat} className="badge-consequence badge-affected">
                      <Icon name="warn" size={11} /> {cat.replace(/_/g, " ")}
                    </span>
                  ))}
                  {impactReport.dependency_evaluations
                    .filter(
                      (e) =>
                        e.status !== "unaffected" &&
                        !impactReport.affected_categories.includes(e.target)
                    )
                    .map((e) => (
                      <span key={e.target} className="badge-consequence badge-affected">
                        <Icon name="warn" size={11} /> {e.target.replace(/_/g, " ")}
                      </span>
                    ))}
                  <span className="badge-consequence badge-affected">
                    <Icon name="warn" size={11} /> Circulation corridor
                  </span>
                  <span className="badge-consequence badge-affected">
                    <Icon name="warn" size={11} /> Budget ({impactReport.price_delta >= 0 ? "+" : ""}
                    {formatMoney(impactReport.price_delta)})
                  </span>
                </div>
              </div>

              <div className="consequence-box unaffected-box">
                <span className="box-title">UNCHANGED &amp; PRESERVED</span>
                <div className="badge-wrap">
                  {impactReport.unaffected_categories.map((cat) => (
                    <span key={cat} className="badge-consequence badge-unaffected">
                      <Icon name="check" size={11} /> {cat.replace(/_/g, " ")}
                    </span>
                  ))}
                  {impactReport.dependency_evaluations
                    .filter(
                      (e) =>
                        e.status === "unaffected" &&
                        !impactReport.unaffected_categories.includes(e.target)
                    )
                    .map((e) => (
                      <span key={e.target} className="badge-consequence badge-unaffected">
                        <Icon name="check" size={11} /> {e.target.replace(/_/g, " ")}
                      </span>
                    ))}
                  <span className="badge-consequence badge-unaffected">
                    <Icon name="check" size={11} /> Door swing
                  </span>
                  <span className="badge-consequence badge-unaffected">
                    <Icon name="check" size={11} /> Room boundary
                  </span>
                </div>
              </div>
            </div>

            {/* 3. 4-Domain Constraint Summary Tiles */}
            <div className="constraint-impact-tiles">
              <div className={`impact-tile tile-${impactReport.spatial_status}`}>
                <span className="tile-name">SPACE</span>
                <span className="tile-status">
                  {impactReport.spatial_status === "pass" ? "Clearances pass" : "Clearance overlap"}
                </span>
              </div>
              <div className={`impact-tile tile-${impactReport.budget_status}`}>
                <span className="tile-name">BUDGET</span>
                <span className="tile-status">
                  {impactReport.price_delta >= 0 ? "+" : ""}
                  {formatMoney(impactReport.price_delta)}
                </span>
              </div>
              <div className={`impact-tile tile-${impactReport.compatibility_status}`}>
                <span className="tile-name">Compatibility</span>
                <span className="tile-status">
                  {impactReport.compatibility_status === "pass" ? "Compatible" : "Interface check"}
                </span>
              </div>
              <div className={`impact-tile tile-${impactReport.installation_status}`}>
                <span className="tile-name">Installation</span>
                <span className="tile-status">
                  {impactReport.installation_status === "pass" ? "Verified" : "Rough-in check"}
                </span>
              </div>
            </div>

            {/* 4. Feasible Actionable Trade-offs */}
            <div className="tradeoffs-container">
              <div className="tradeoffs-header">
                <span className="tradeoffs-title">Trade-offs you could take</span>
                <span className="tradeoffs-subtitle">
                  Choose a deterministic resolution to apply and construct Version 2:
                </span>
              </div>

              <div className="tradeoff-cards-list">
                {impactReport.candidate_tradeoffs.map((option, index) => {
                  const isSelected =
                    selectedTradeoffId === option.id ||
                    (selectedTradeoffId === null && index === 0);

                  return (
                    <div
                      key={option.id}
                      className={`tradeoff-card-item ${isSelected ? "selected" : ""}`}
                      onClick={() => setSelectedTradeoffId(option.id)}
                      role="radio"
                      aria-checked={isSelected}
                      tabIndex={0}
                    >
                      <div className="card-top-row">
                        <span className="option-letter">Option {String.fromCharCode(65 + index)}</span>
                        <span className={`strategy-pill strategy-${option.strategy}`}>
                          {option.strategy.replace(/_/g, " ")}
                        </span>
                      </div>

                      <h4 className="option-title">{option.title}</h4>
                      <p className="option-desc">{option.description}</p>

                      <div className="option-substitutions-list">
                        {option.substitutions.map((sub, sIdx) => (
                          <div key={sIdx} className="sub-row">
                            <span className="sub-cat">{sub.category}:</span>
                            <span className="sub-action">Swap {sub.remove_id.replace(/_/g, " ")} → {sub.add_id.replace(/_/g, " ")}</span>
                          </div>
                        ))}
                      </div>

                      <div className="option-metrics-footer">
                        <span className="option-cost-delta">
                          Cost: {option.price_delta >= 0 ? "+" : ""}
                          {formatMoney(option.price_delta)}
                        </span>
                        <span className="option-feasibility-tag">
                          {option.resulting_is_feasible ? "Guaranteed feasible" : "Infeasible"}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Action Buttons: Apply, Compare, Keep Current */}
              <div className="tradeoff-apply-actions">
                <button
                  type="button"
                  className="btn-apply-tradeoff-primary"
                  disabled={busy || impactReport.candidate_tradeoffs.length === 0}
                  onClick={() => {
                    const chosen =
                      impactReport.candidate_tradeoffs.find(
                        (o) => o.id === selectedTradeoffId
                      ) || impactReport.candidate_tradeoffs[0];
                    if (chosen) onApplyTradeoff(chosen);
                  }}
                >
                  <Icon name="check" size={14} /> Apply change &amp; construct version 2
                </button>

                <div className="secondary-actions-row">
                  {onCompareVersions && (
                    <button
                      type="button"
                      className="btn-copilot-secondary"
                      onClick={onCompareVersions}
                    >
                      Compare V1 vs V2
                    </button>
                  )}
                  {onKeepCurrent && (
                    <button
                      type="button"
                      className="btn-copilot-secondary"
                      onClick={onKeepCurrent}
                    >Keep the baseline</button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="copilot-empty-placeholder">
            <div className="copilot-empty-icon">
              <Icon name="pulse" size={22} />
            </div>
            <h4 className="copilot-empty-title">Nothing to evaluate yet</h4>
            <p className="copilot-empty-desc">
              Describe a change above, or pick one of the suggestions. Every clearance, plumbing
              line and price is recomputed before anything is committed — so you see the cost of a
              decision before you make it.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
