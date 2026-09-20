import { useState } from "react";
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
  space: "Space",
  budget: "Budget",
  compatibility: "Compatibility",
  installation: "Installation",
  style: "Style",
  water: "Water",
  verification: "Verification",
};

interface Props {
  ledger: ConstraintLedger;
}

export function ConstraintLedgerPanel({ ledger }: Props) {
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null);

  const getOverallBadge = () => {
    switch (ledger.overall_status) {
      case "feasible":
        return <span className="ledger-verdict verdict-pass">✓ Feasible</span>;
      case "feasible_pending_verification":
        return (
          <span className="ledger-verdict verdict-warn">
            ⚠ Feasible (Pending Verification)
          </span>
        );
      case "infeasible":
        return <span className="ledger-verdict verdict-fail">✗ Infeasible</span>;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: LedgerStatus) => {
    switch (status) {
      case "pass":
        return <span className="status-badge status-pass">Pass</span>;
      case "warning":
        return <span className="status-badge status-warn">Warning</span>;
      case "fail":
        return <span className="status-badge status-fail">Violation</span>;
    }
  };

  const domainOrder = [
    "space",
    "budget",
    "compatibility",
    "installation",
    "style",
    "water",
    "verification",
  ];

  return (
    <section className="panel ledger-panel">
      <div className="ledger-header">
        <div>
          <h2>Constraint Ledger</h2>
          <p className="hint">
            Deterministic architectural health across 7 functional domains. All verdicts
            are verified against catalog specifications, physical clearances, and local code.
          </p>
        </div>
        <div className="ledger-overall">{getOverallBadge()}</div>
      </div>

      <div className="ledger-grid">
        {domainOrder.map((domainKey) => {
          const entry = ledger.domains[domainKey];
          if (!entry) return null;
          const isExpanded = expandedDomain === domainKey;

          return (
            <div
              key={domainKey}
              className={`ledger-card ledger-card-${entry.status} ${
                isExpanded ? "expanded" : ""
              }`}
              onClick={() => setExpandedDomain(isExpanded ? null : domainKey)}
            >
              <div className="ledger-card-top">
                <span className="domain-icon">{DOMAIN_ICONS[domainKey] ?? "•"}</span>
                <span className="domain-title">
                  {DOMAIN_LABELS[domainKey] ?? domainKey.toUpperCase()}
                </span>
                {getStatusBadge(entry.status)}
              </div>
              <p className="ledger-card-summary">{entry.summary}</p>
              {entry.checks && entry.checks.length > 0 && (
                <span className="ledger-details-toggle">
                  {isExpanded ? "Hide details ▲" : `${entry.checks.length} checks ▼`}
                </span>
              )}

              {isExpanded && entry.checks && entry.checks.length > 0 && (
                <div className="ledger-checks-list">
                  {entry.checks.map((chk, idx) => (
                    <div
                      key={idx}
                      className={`ledger-check-item check-${chk.status}`}
                    >
                      <span className="check-indicator">
                        {chk.status === "pass"
                          ? "✓"
                          : chk.status === "fail"
                          ? "✗"
                          : "⚠"}
                      </span>
                      <div className="check-body">
                        <strong>{chk.constraint.replace(/_/g, " ")}</strong>
                        <p>{chk.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
