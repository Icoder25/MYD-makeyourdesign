import { formatLitres, formatMoney } from "../api";
import type { CandidatePlan } from "../types";

const LABELS: Record<string, string> = {
  recommended: "Recommended",
  budget_focused: "Lowest cost",
  sustainability_focused: "Most water-efficient",
  alternative: "Alternative",
};

function StatusPill({ status }: { status: string }) {
  if (status === "feasible") {
    return <span className="pill pill-ok">All checks passed</span>;
  }
  if (status === "feasible_pending_verification") {
    return <span className="pill pill-warn">Pending verification</span>;
  }
  return <span className="pill pill-bad">Not feasible</span>;
}

interface Props {
  candidate: CandidatePlan;
  selected: boolean;
  onSelect: () => void;
}

export function CandidateCard({ candidate, selected, onSelect }: Props) {
  const water = candidate.water_impact;
  const report = candidate.constraint_report;

  return (
    <article
      className={selected ? "card card-selected" : "card"}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onSelect();
      }}
    >
      <header className="card-head">
        <h3>{LABELS[candidate.label ?? ""] ?? "Option"}</h3>
        <StatusPill status={report.status} />
      </header>

      <div className="price-row">
        <span className="price">{formatMoney(candidate.total_price, candidate.currency)}</span>
        {candidate.remaining_budget !== null && (
          <span className="remaining">
            {formatMoney(candidate.remaining_budget, candidate.currency)} left
          </span>
        )}
      </div>

      <ul className="product-list">
        {candidate.products.map((product) => (
          <li key={product.id}>
            <span className="product-name">{product.name}</span>
            <span className="product-meta">
              {product.price !== null && formatMoney(product.price, product.currency)}
              {product.water.watersense_eligible === true && (
                <span className="tag tag-eco" title="Recorded flow meets the WaterSense threshold. Eligibility computed, not a certification claim.">
                  efficient
                </span>
              )}
              {product.smart.features.length > 0 && <span className="tag tag-smart">smart</span>}
            </span>
          </li>
        ))}
      </ul>

      {water.status === "calculated" && water.percent_saved !== null && (
        <p className="water-line">
          {formatLitres(water.configuration_annual_litres ?? 0)}/year —{" "}
          {water.percent_saved > 0 ? (
            <strong>{water.percent_saved.toFixed(0)}% below baseline</strong>
          ) : (
            <span>no saving against baseline</span>
          )}
        </p>
      )}

      {candidate.explanation && <p className="explanation">{candidate.explanation}</p>}

      {report.verification_requirements.length > 0 && (
        <details className="verify">
          <summary>
            {report.verification_requirements.length} item(s) to verify before ordering
          </summary>
          <ul>
            {report.verification_requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      )}

      <details className="score">
        <summary>Why it ranked here</summary>
        <div className="score-grid">
          {(
            [
              ["Spatial fit", candidate.score.spatial],
              ["Budget use", candidate.score.budget],
              ["Water efficiency", candidate.score.water_efficiency],
              ["Style match", candidate.score.style],
              ["Smart features", candidate.score.smart_feature],
              ["Preferences", candidate.score.preference],
            ] as const
          ).map(([name, value]) => (
            <div key={name} className="score-row">
              <span>{name}</span>
              <span className="bar">
                <span className="bar-fill" style={{ width: `${Math.round(value * 100)}%` }} />
              </span>
              <span className="score-num">{value.toFixed(2)}</span>
            </div>
          ))}
        </div>
        {candidate.strengths.map((item) => (
          <p key={item} className="strength">
            + {item}
          </p>
        ))}
        {candidate.trade_offs.map((item) => (
          <p key={item} className="tradeoff">
            − {item}
          </p>
        ))}
      </details>
    </article>
  );
}
