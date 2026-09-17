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

      {visionError && <p className="inline-note">Image analysis unavailable: {visionError}</p>}

      {vision && (
        <>
          <h3>From your photo</h3>
          <div className="confidence">
            <span className="confidence-label">
              Overall confidence {(vision.overall_confidence * 100).toFixed(0)}%
            </span>
            <span className="confidence-bar">
              <span
                className="confidence-fill"
                style={{ width: `${vision.overall_confidence * 100}%` }}
              />
            </span>
          </div>

          {vision.detected_objects.length > 0 && (
            <ul className="detected">
              {vision.detected_objects.map((object, index) => (
                <li key={index}>
                  <span>{object.type.replace(/_/g, " ")}</span>
                  <span className="muted">{(object.confidence * 100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
          )}

          {vision.ambiguous_objects.length > 0 && (
            <>
              <h4>Ambiguous</h4>
              <ul className="notes">
                {vision.ambiguous_objects.map((item, index) => (
                  <li key={index}>
                    Could be {item.candidate_types.join(" or ")} — {item.reason}
                  </li>
                ))}
              </ul>
            </>
          )}

          <h4>What a photograph cannot establish</h4>
          <ul className="unverifiable">
            {Object.entries(vision.unverifiable_attributes).map(([key, value]) => (
              <li key={key}>
                <strong>{key.replace(/_/g, " ")}</strong>: unknown — {value.reason}
              </li>
            ))}
          </ul>
          <p className="hint">
            Image evidence is advisory only. It never reaches the constraint engine, and it
            cannot supply a dimension, a rough-in, or an electrical fact. Your measurements
            remain the only source of truth.
          </p>
        </>
      )}
    </section>
  );
}
