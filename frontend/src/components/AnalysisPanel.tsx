import type { PlanMeta, VisionEvidence } from "../types";

/**
 * Screen 2: what the system knows, what it estimated, and what it refuses to
 * claim. This panel exists to make the uncertainty visible rather than let a
 * confident-looking result imply certainty it does not have.
 */

interface Props {
  meta: PlanMeta;
  vision: VisionEvidence | null;
  visionError: string | null;
}

export function AnalysisPanel({ meta, vision, visionError }: Props) {
  return (
    <section className="panel">
      <h2>2 · What the system knows</h2>

      <div className="stat-row">
        <div className="stat">
          <span className="stat-num">{meta.catalog_size}</span>
          <span className="stat-label">products in catalog</span>
        </div>
        <div className="stat">
          <span className="stat-num">{meta.configurations_evaluated.toLocaleString()}</span>
          <span className="stat-label">configurations evaluated</span>
        </div>
        <div className="stat">
          <span className="stat-num">{meta.computed_by.length}</span>
          <span className="stat-label">deterministic engines</span>
        </div>
      </div>

      <p className="computed-by">
        Computed by: {meta.computed_by.map((item) => item.replace(/_/g, " ")).join(", ")}.
        No figure on this page was produced by a language model.
      </p>

      {meta.notes.length > 0 && (
        <>
          <h3>Unknowns carried forward</h3>
          <ul className="notes">
            {meta.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </>
      )}

      {visionError && (
        <div className="callout callout-warning" style={{ margin: "14px 0", fontSize: "13px" }}>
          <strong>Vision Advisory Notice:</strong> Vision analysis unavailable. You can continue using manual project inputs.
        </div>
      )}

      {vision && (
        <>
          <h3>From your photo</h3>
          <div className="confidence">
            <span className="confidence-label">
              Visual confidence index: {(vision.overall_confidence * 100).toFixed(0)}%
            </span>
            <span className="confidence-bar">
              <span
                className="confidence-fill"
                style={{ width: `${vision.overall_confidence * 100}%` }}
              />
            </span>
          </div>
          <p style={{ fontSize: "11px", color: "var(--ink-500)", margin: "4px 0 12px" }}>
            Confidence represents an application classification heuristic, not physical certainty.
          </p>

          {vision.detected_objects.length > 0 && (
            <ul className="detected" style={{ listStyle: "none", padding: 0 }}>
              {vision.detected_objects.map((object, index) => {
                const isObserved = (object.observation_status || (object.confidence >= 0.7 ? "observed" : "estimated")) === "observed";
                return (
                  <li
                    key={index}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "8px 10px",
                      background: "#fff",
                      border: "1px solid var(--line)",
                      borderRadius: "6px",
                      marginBottom: "6px",
                      fontSize: "12px",
                    }}
                  >
                    <div>
                      <strong style={{ textTransform: "capitalize", color: "var(--ink)" }}>
                        {object.type.replace(/_/g, " ")}
                      </strong>
                      <span
                        style={{
                          marginLeft: "8px",
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          textTransform: "uppercase",
                          background: isObserved ? "var(--ok-soft, #dcfce7)" : "var(--warn-soft, #fef9c3)",
                          color: isObserved ? "var(--ok, #166534)" : "var(--warn, #854d0e)",
                        }}
                      >
                        {isObserved ? "Observed" : "Estimated"}
                      </span>
                      {object.approximate_wall_region && object.approximate_wall_region !== "unknown" && (
                        <span style={{ marginLeft: "8px", fontSize: "11px", color: "var(--ink-soft)" }}>
                          (Advisory: {object.approximate_wall_region} wall)
                        </span>
                      )}
                    </div>
                    <div style={{ textAlign: "right", fontSize: "11px", color: "var(--ink-soft)" }}>
                      {(object.confidence * 100).toFixed(0)}% confidence · Dimensions: Unmeasured
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          {vision.ambiguous_objects.length > 0 && (
            <>
              <h4>Ambiguous visual elements</h4>
              <ul className="notes">
                {vision.ambiguous_objects.map((item, index) => (
                  <li key={index}>
                    Could be {item.candidate_types.join(" or ")} — {item.reason}
                  </li>
                ))}
              </ul>
            </>
          )}

          <h4>What a photograph cannot establish (Requires Verification)</h4>
          <ul className="unverifiable">
            {Object.entries(vision.unverifiable_attributes).map(([key, value]) => (
              <li key={key}>
                <strong>{key.replace(/_/g, " ")}</strong>: requires physical verification — {value.reason}
              </li>
            ))}
          </ul>
          <p className="hint">
            Visual observations are advisory only. They map to verification requirements in the Constraint Ledger,
            never to constraint failure. Your measured room dimensions and confirmed rough-ins remain the authoritative source of truth.
          </p>
        </>
      )}
    </section>
  );
}
