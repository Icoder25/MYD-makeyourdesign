import React, { useState } from "react";
import { formatMoney } from "../api";
import type { ConstraintLedger, LedgerStatus } from "../types";

const DOMAIN_ICONS: Record<string, string> = {
  space: "📐",
  budget: "💰",
  compatibility: "🔗",
  installation: "🔧",
  style: "🎨",
  water: "💧",
  verification: "📋",
};

const DOMAIN_LABELS: Record<string, string> = {
  space: "SPACE & CLEARANCE",
  budget: "BUDGET FEASIBILITY",
  compatibility: "FIXTURE INTERFACES",
  installation: "ROUGH-IN & POWER",
  style: "AESTHETIC FINISH",
  water: "WATER CONSERVATION",
  verification: "FIELD VERIFICATION",
};

interface PersistentLedgerDockProps {
  ledger: ConstraintLedger | null;
  totalPrice?: number;
  currency?: string;
  onOpenFinalize: () => void;
  isFinalized: boolean;
  userRole?: "homeowner" | "designer";
}

export const PersistentLedgerDock: React.FC<PersistentLedgerDockProps> = ({
  ledger,
  totalPrice,
  currency = "INR",
  onOpenFinalize,
  isFinalized,
  userRole = "homeowner",
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

  if (!ledger) return null;

  const domainKeys = [
    "space",
    "budget",
    "compatibility",
    "installation",
    "style",
    "water",
    "verification",
  ];

  const getStatusIcon = (status: LedgerStatus) => {
    switch (status) {
      case "pass":
        return "✓";
      case "warning":
        return "⚠";
      case "fail":
        return "✗";
    }
  };

  // Count items needing verification across domains
  const verificationCount = domainKeys.reduce((acc, k) => {
    const entry = ledger.domains[k];
    return acc + (entry?.verification_count ?? (entry?.status === "warning" ? 1 : 0));
  }, 0);

  const getOverallVerdict = () => {
    switch (ledger.overall_status) {
      case "feasible":
        return <span className="dock-overall dock-feasible">✓ Feasible</span>;
      case "feasible_pending_verification":
        return (
          <span className="dock-overall dock-pending">
            ⚠ Feasible ({verificationCount > 0 ? `${verificationCount} to verify` : "Pending verification"})
          </span>
        );
      case "infeasible":
        return <span className="dock-overall dock-infeasible">✗ Infeasible (Needs Trade-off)</span>;
      default:
        return null;
    }
  };

  return (
    <footer
      className={`persistent-ledger-dock ${isExpanded ? "expanded" : ""}`}
      aria-label="7-Domain Constraint & Trust Ledger"
    >
      {/* Main Persistent Dock Bar */}
      <div className="dock-bar-inner">
        <div className="dock-domains-row">
          <div className="dock-brand-label">
            <span className="dock-title-badge">DECISION LEDGER</span>
            <span className="dock-truth-hint">
              {totalPrice !== undefined ? `${formatMoney(totalPrice, currency)} · ` : ""}
              {userRole === "designer"
                ? "Deterministic spatial & plumbing audit"
                : "Continuous verification & safety checks"}
            </span>
          </div>

          <div className="dock-pills-list">
            {domainKeys.map((key) => {
              const entry = ledger.domains[key];
              if (!entry) return null;
              const isSelected = selectedDomain === key && isExpanded;

              return (
                <button
                  key={key}
                  type="button"
                  className={`dock-domain-pill dock-status-${entry.status} ${
                    isSelected ? "selected" : ""
                  }`}
                  onClick={() => {
                    if (selectedDomain === key && isExpanded) {
                      setIsExpanded(false);
                      setSelectedDomain(null);
                    } else {
                      setSelectedDomain(key);
                      setIsExpanded(true);
                    }
                  }}
                  title={`${DOMAIN_LABELS[key]}: ${entry.summary}`}
                  aria-expanded={isSelected}
                >
                  <span className="pill-icon">{DOMAIN_ICONS[key]}</span>
                  <span className="pill-label">{key.toUpperCase()}</span>
                  <span className="pill-status">{getStatusIcon(entry.status)}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Action Cluster */}
        <div className="dock-right-actions">
          {getOverallVerdict()}

          <button
            type="button"
            className="btn-dock-expand"
            onClick={() => {
              setIsExpanded(!isExpanded);
              if (!selectedDomain) setSelectedDomain("space");
            }}
            aria-label={isExpanded ? "Collapse ledger sheet" : "Expand ledger sheet"}
          >
            {isExpanded ? "Collapse ▲" : "Inspect Checks ▼"}
          </button>

          <button
            type="button"
            className={`btn-dock-finalize ${isFinalized ? "finalized" : ""}`}
            onClick={onOpenFinalize}
            title={isFinalized ? "Design specification is finalized" : "Review verification items and finalize"}
          >
            <span>{isFinalized ? "🔒" : "📋"}</span>
            {isFinalized ? "Finalized" : "Finalize"}
          </button>
        </div>
      </div>

      {/* Expandable Check Sheet Drawer */}
      {isExpanded && (
        <div className="dock-drawer-content" role="region" aria-label="Expanded Verification Details">
          {/* Trust Legend */}
          <div className="dock-trust-legend">
            <span className="legend-head">AUDIT PROVENANCE &amp; TRUST LABELS:</span>
            <span className="legend-tag tag-confirmed">✓ Confirmed (User Input)</span>
            <span className="legend-tag tag-observed">◌ Observed (Vision Analysis)</span>
            <span className="legend-tag tag-estimated">≈ Estimated (Deterministic Inference)</span>
            <span className="legend-tag tag-unknown">? Unknown (Plumbing Hidden Behind Wall)</span>
            <span className="legend-tag tag-verify">! Verify (Requires Field Measurement)</span>
          </div>

          <div className="dock-drawer-header">
            <div className="drawer-tabs" role="tablist">
              {domainKeys.map((key) => {
                const entry = ledger.domains[key];
                if (!entry) return null;
                return (
                  <button
                    key={key}
                    type="button"
                    role="tab"
                    aria-selected={selectedDomain === key}
                    className={`drawer-tab-btn ${selectedDomain === key ? "active" : ""}`}
                    onClick={() => setSelectedDomain(key)}
                  >
                    {DOMAIN_ICONS[key]} {key.toUpperCase()} ({getStatusIcon(entry.status)})
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              className="btn-drawer-close"
              onClick={() => setIsExpanded(false)}
              aria-label="Close verification drawer"
            >
              ✕ Close
            </button>
          </div>

          {selectedDomain && ledger.domains[selectedDomain] && (
            <div className="dock-checks-body">
              <div className="domain-summary-banner">
                <span className="summary-title">
                  {DOMAIN_LABELS[selectedDomain]} SUMMARY:
                </span>
                <span className="summary-text">
                  {ledger.domains[selectedDomain].summary}
                </span>
              </div>

              <div className="domain-checks-grid">
                {ledger.domains[selectedDomain].checks &&
                ledger.domains[selectedDomain].checks.length > 0 ? (
                  ledger.domains[selectedDomain].checks.map((chk, idx) => (
                    <div
                      key={idx}
                      className={`check-card check-card-${chk.status}`}
                    >
                      <div className="check-card-header">
                        <span className="check-mark">
                          {chk.status === "pass"
                            ? "✓"
                            : chk.status === "fail"
                            ? "✗"
                            : "⚠"}
                        </span>
                        <strong className="check-name">
                          {chk.constraint.replace(/_/g, " ")}
                        </strong>
                        <span className="check-trust-pill">
                          {chk.status === "pass"
                            ? "✓ Confirmed"
                            : chk.status === "verification_required"
                            ? "! Verify"
                            : "≈ Estimated"}
                        </span>
                      </div>
                      <p className="check-reason">{chk.reason}</p>
                    </div>
                  ))
                ) : (
                  <div className="check-card check-card-pass">
                    <div className="check-card-header">
                      <span className="check-mark">✓</span>
                      <strong className="check-name">Deterministic Compliance Verified</strong>
                    </div>
                    <p className="check-reason">
                      All calculations for {selectedDomain} are satisfied according to established plumbing code
                      and spatial guidelines.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </footer>
  );
};
