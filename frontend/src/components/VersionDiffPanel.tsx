import { formatMoney } from "../api";
import type { DesignState, DesignStateDiff } from "../types";

interface Props {
  diff: DesignStateDiff;
  v1State?: DesignState | null;
  v2State?: DesignState | null;
}

export function VersionDiffPanel({ diff, v1State, v2State }: Props) {
  const v1Price = v1State?.total_price;
  const v2Price = v2State?.total_price;

  // Extract decision rationale from v2 decisions if available
  const latestDecision = v2State?.decision_records?.slice(-1)[0];
  const rationale =
    latestDecision?.rationale ??
    "Trade-off applied to maintain architectural feasibility and budget limits.";

  return (
    <section className="panel diff-panel">
      <div className="diff-header">
        <h2>What changed between versions</h2>
        <span className="version-tag">
          {diff.from_version.toUpperCase()} → {diff.to_version.toUpperCase()}
        </span>
      </div>

      <p className="hint">
        Deterministic arithmetic and fixture delta computed directly from the DesignState
        snapshots. No regeneration occurred.
      </p>

      {/* Version Price Transition */}
      <div className="diff-transition-banner">
        <div className="transition-box">
          <span className="trans-ver">VERSION {diff.from_version.toUpperCase()}</span>
          <span className="trans-val">
            {v1Price !== undefined ? formatMoney(v1Price) : "Baseline"}
          </span>
        </div>

        <div className="transition-arrow">
          <span>↓</span>
          <span className={`trans-delta ${diff.price_delta <= 0 ? "delta-saved" : "delta-added"}`}>
            {diff.price_delta >= 0 ? "+" : ""}
            {formatMoney(diff.price_delta)}
          </span>
        </div>

        <div className="transition-box active-ver-box">
          <span className="trans-ver">VERSION {diff.to_version.toUpperCase()} (ACTIVE)</span>
          <span className="trans-val">
            {v2Price !== undefined ? formatMoney(v2Price) : "New design"}
          </span>
        </div>
      </div>

      {/* Fixture Changes (Added, Removed, Modified) */}
      <div className="diff-grid">
        <div className="diff-col">
          <h4>Changed</h4>
          {diff.modified_categories.length > 0 ? (
            <ul className="diff-list">
              {diff.modified_categories.map((cat) => (
                <li key={cat}>
                  <strong>{cat.toUpperCase()}:</strong> replaced with alternate specification
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-msg">No fixture categories changed.</p>
          )}
        </div>

        <div className="diff-col added-col">
          <h4>Added</h4>
          {diff.added_products.length > 0 ? (
            <ul className="diff-list">
              {diff.added_products.map((p) => (
                <li key={p.id}>
                  <span className="icon-plus">+</span>
                  <div>
                    <strong>{p.name}</strong>
                    <span className="prod-price">{formatMoney(p.price || 0)}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-msg">None</p>
          )}
        </div>

        <div className="diff-col removed-col">
          <h4>Removed</h4>
          {diff.removed_products.length > 0 ? (
            <ul className="diff-list">
              {diff.removed_products.map((p) => (
                <li key={p.id}>
                  <span className="icon-minus">-</span>
                  <div>
                    <strong>{p.name}</strong>
                    <span className="prod-price">{formatMoney(p.price || 0)}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-msg">None</p>
          )}
        </div>
      </div>

      {/* Decision Memory Rationale */}
      <div className="diff-rationale-box">
        <span className="rationale-label">Why this changed</span>
        <p className="rationale-text">&ldquo;{rationale}&rdquo;</p>
      </div>
    </section>
  );
}
