import { useState } from "react";
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
        return <span className="ledger-verdict verdict-pass">
        <Icon name="check" size={13} /> Feasible
      </span>;
      case "feasible_pending_verification":
        return (
          <span className="ledger-verdict verdict-warn">
            <Icon name="warn" size={13} /> Feasible — pending verification
          </span>
        );
      case "infeasible":
        return <span className="ledger-verdict verdict-fail">
        <Icon name="cross" size={13} /> Infeasible
      </span>;
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
          <h2>Constraint ledger</h2>
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
                <span className="domain-icon">
            <Icon name={DOMAIN_ICONS[domainKey] ?? "dot"} size={14} />
          </span>
                <span className="domain-title">
                  {DOMAIN_LABELS[domainKey] ?? domainKey.toUpperCase()}
                </span>
                {getStatusBadge(entry.status)}
              </div>
              <p className="ledger-card-summary">{entry.summary}</p>
              {entry.checks && entry.checks.length > 0 && (
                <span className="ledger-details-toggle">
                  {isExpanded ? (
              <>
                Hide details <Icon name="caretUp" size={11} />
              </>
            ) : (
              <>
                {entry.checks.length} checks <Icon name="caretDown" size={11} />
              </>
            )}
                </span>
              )}

              {isExpanded && entry.checks && entry.checks.length > 0 && (
                <div className="ledger-checks-list">
                  {entry.checks.map((chk, idx) => (
                    <div
                      key={idx}
                      className={`ledger-check-item check-${chk.status}`}
                    >
                      <Icon
                        className="check-indicator"
                        size={12}
                        name={
                          chk.status === "pass"
                            ? "check"
                            : chk.status === "fail"
                            ? "cross"
                            : "warn"
                        }
                      />
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
