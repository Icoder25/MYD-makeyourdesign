import { formatLitres } from "../api";
import type { WaterImpactEstimate } from "../types";

export function WaterPanel({ water }: { water: WaterImpactEstimate }) {
  if (water.status === "insufficient_data") {
    return (
      <section className="panel">
        <h2>Water impact</h2>
        <p className="inline-note">
          Not enough recorded flow data to estimate water use for this configuration.
          {water.unquantified_products.length > 0 && (
            <> Missing figures for: {water.unquantified_products.join(", ")}.</>
          )}
        </p>
        <p className="hint">{water.disclaimer}</p>
      </section>
    );
  }

  const saved = water.annual_litres_saved ?? 0;
  const percent = water.percent_saved ?? 0;
  const configured = water.configuration_annual_litres ?? 0;
  const baseline = water.baseline_annual_litres ?? 0;
  const barWidth = baseline > 0 ? Math.min(100, (configured / baseline) * 100) : 100;

  return (
    <section className="panel">
      <h2>Water impact</h2>

      <div className="water-headline">
        <div>
          <span className="water-number">{formatLitres(configured)}</span>
          <span className="water-caption">estimated per year</span>
        </div>
        {saved > 0 && (
          <div className="water-saving">
            <span className="water-number">{percent.toFixed(0)}%</span>
            <span className="water-caption">below baseline · {formatLitres(saved)} saved</span>
          </div>
        )}
      </div>

      <div className="water-bars">
        <div className="water-bar-row">
          <span>This configuration</span>
          <span className="water-bar">
            <span className="water-bar-fill" style={{ width: `${barWidth}%` }} />
          </span>
          <span>{formatLitres(configured)}</span>
        </div>
        <div className="water-bar-row">
          <span>Regulatory baseline</span>
          <span className="water-bar">
            <span className="water-bar-fill water-bar-baseline" style={{ width: "100%" }} />
          </span>
          <span>{formatLitres(baseline)}</span>
        </div>
      </div>

      <p className="hint">{water.baseline_description}</p>

      <details className="water-detail">
        <summary>How each figure was calculated</summary>
        <table className="water-table">
          <thead>
            <tr>
              <th>Fixture</th>
              <th>Recorded spec</th>
              <th>Per year</th>
              <th>Formula</th>
            </tr>
          </thead>
          <tbody>
            {water.fixtures
              .filter((fixture) => fixture.status !== "not_a_water_fixture")
              .map((fixture) => (
                <tr key={fixture.product_name}>
                  <td>{fixture.product_name}</td>
                  <td>{fixture.recorded_spec ?? "—"}</td>
                  <td>{fixture.annual_litres ? formatLitres(fixture.annual_litres) : "—"}</td>
                  <td className="formula">{fixture.formula ?? fixture.note}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </details>

      <details className="water-detail">
        <summary>Assumptions this estimate depends on</summary>
        <ul>
          {water.assumptions.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
      </details>

      {water.manufacturer_claims.length > 0 && (
        <div className="claims">
          <h3>Manufacturer claims (not included in the figures above)</h3>
          {water.manufacturer_claims.map((claim) => (
            <blockquote key={claim.source_url}>
              <p>
                Manufacturer states <strong>up to {claim.value}%</strong> saving versus{" "}
                {claim.comparison_baseline}.
              </p>
              <p className="hint">{claim.assumptions}</p>
              <a href={claim.source_url} target="_blank" rel="noreferrer">
                Manufacturer source
              </a>
            </blockquote>
          ))}
          <p className="hint">
            This is the manufacturer's own claim, reproduced with its stated baseline and
            caveats. It is deliberately excluded from the calculated totals above, which
            use only recorded flow rates.
          </p>
        </div>
      )}

      <p className="hint disclaimer">{water.disclaimer}</p>
    </section>
  );
}
