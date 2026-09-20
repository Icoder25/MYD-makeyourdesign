import React, { useState } from "react";
import { formatMoney } from "../api";
import type { ConstraintLedger, LedgerStatus } from "../types";
import { Icon, type IconName } from "./Icon";

const DOMAIN_ICONS: Record<string, IconName> = {
  space: "plan",
  budget: "money",
  compatibility: "link",
  installation: "wrench",
  style: "palette",
  water: "drop",
  verification: "clipboard",
};

const DOMAIN_LABELS: Record<string, string> = {
  space: "Space & clearance",
  budget: "Budget feasibility",
  compatibility: "Fixture interfaces",
  installation: "Rough-in & power",
  style: "Aesthetic finish",
  water: "Water conservation",
  verification: "Field verification",
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

  const getStatusIcon = (status: LedgerStatus): IconName => {
    switch (status) {
      case "warning":
        return "warn";
      case "fail":
        return "cross";
      default:
        return "check";
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
        return <span className="dock-overall dock-feasible">
        <Icon name="check" size={12} /> Feasible
      </span>;
      case "feasible_pending_verification":
        return (
          <span className="dock-overall dock-pending">
            <Icon name="warn" size={12} /> Feasible ({verificationCount > 0 ? `${verificationCount} to verify` : "pending verification"})
          </span>
        );
      case "infeasible":
        return <span className="dock-overall dock-infeasible">
        <Icon name="cross" size={12} /> Infeasible — needs a trade-off
      </span>;
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
            <span className="dock-title-badge">Decision ledger</span>
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
                  <Icon className="pill-icon" name={DOMAIN_ICONS[key]} size={12} />
                  <span className="pill-label">{key}</span>
                  <Icon className="pill-status" name={getStatusIcon(entry.status)} size={11} />
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
            {isExpanded ? (
          <>
            Collapse <Icon name="caretUp" size={10} />
          </>
        ) : (
          <>
            Inspect checks <Icon name="caretDown" size={10} />
          </>
        )}
          </button>

          <button
            type="button"
            className={`btn-dock-finalize ${isFinalized ? "finalized" : ""}`}
            onClick={onOpenFinalize}
            title={isFinalized ? "Design specification is finalized" : "Review verification items and finalize"}
          >
            <Icon name={isFinalized ? "lock" : "clipboard"} size={12} />
            {isFinalized ? "Finalized" : "Finalize"}
          </button>
        </div>
      </div>

      {/* Expandable Check Sheet Drawer */}
      {isExpanded && (
        <div className="dock-drawer-content" role="region" aria-label="Verification detail">
          {/* Trust Legend */}
          <div className="dock-trust-legend">
            <span className="legend-head">Provenance</span>
            <span className="legend-tag tag-confirmed">
              <Icon name="check" size={11} /> Confirmed — your input
            </span>
            <span className="legend-tag tag-observed">
              <Icon name="eye" size={11} /> Observed — vision analysis
            </span>
            <span className="legend-tag tag-estimated">
              ≈ Estimated — deterministic inference
            </span>
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
                    <Icon name={DOMAIN_ICONS[key]} size={11} />
                    <span>{key}</span>
                    <Icon name={getStatusIcon(entry.status)} size={10} />
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
              <Icon name="close" size={11} /> Close
            </button>
          </div>

          {selectedDomain && ledger.domains[selectedDomain] && (
            <div className="dock-checks-body">
              <div className="domain-summary-banner">
                <span className="summary-title">
                  {DOMAIN_LABELS[selectedDomain]}
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
                        <Icon
                          className="check-mark"
                          size={12}
                          name={
                            chk.status === "pass"
                              ? "check"
                              : chk.status === "fail"
                              ? "cross"
                              : "warn"
                          }
                        />
                        <strong className="check-name">
                          {chk.constraint.replace(/_/g, " ")}
                        </strong>
                        <span className="check-trust-pill">
                          {chk.status === "pass"
                            ? "Confirmed"
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
                      <Icon name="check" size={12} className="check-mark" />
                      <strong className="check-name">Compliance verified</strong>
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
