import { useState } from "react";
import { formatMoney } from "../api";
import type { BathroomBrief, ConflictResult, RelaxationSuggestion } from "../types";

/**
 * The product's defining screen.
 *
 * When the requirements cannot all hold at once, the system does not quietly
 * pick something close and present it as an answer. It states what broke, how
 * far off it was, and which specific relaxations were actually evaluated — then
 * hands the decision back to the user.
 */

const CONSTRAINT_NAMES: Record<string, string> = {
  budget: "Budget",
  layout_fit: "Physical space",
  circulation: "Movement around the room",
  fixture_zone_fit: "Fixture zones",
  spatial_fit: "Room envelope",
  compatibility: "Product compatibility",
  installation: "Installation requirements",
  electrical: "Electrical supply",
  category_requirements: "Requested fixtures",
  user_constraints: "Your stated constraints",
};

interface Props {
  conflict: ConflictResult;
  brief: BathroomBrief;
  onResolve: (body: Record<string, unknown>) => void;
  busy: boolean;
}

/** Map a suggestion onto the deterministic resolve action it corresponds to. */
function actionFor(
  suggestion: RelaxationSuggestion,
  brief: BathroomBrief,
): { body: Record<string, unknown>; cta: string } | null {
  const text = suggestion.description;

  if (suggestion.constraint === "budget") {
    const match = text.match(/at least ([\d.]+)/);
    const increase = match ? Math.ceil(Number(match[1])) : 0;
    const target = Math.ceil(((brief.budget ?? 0) + increase) / 1000) * 1000;
    return {
      body: { relaxation: "increase_budget", budget: target },
      cta: `Raise budget to ${formatMoney(target, brief.currency)}`,
    };
  }

  if (suggestion.constraint === "category_requirements") {
    const match = text.match(/'([a-z_]+)'/);
    if (match && brief.required_categories.includes(match[1])) {
      return {
        body: { relaxation: "drop_category", category: match[1] },
        cta: `Drop ${match[1].replace(/_/g, " ")}`,
      };
    }
  }

  if (suggestion.constraint === "layout_fit") {
    const match = text.match(/the ([a-z_]+)\./);
    if (match && brief.required_categories.includes(match[1])) {
      return {
        body: { relaxation: "drop_category", category: match[1] },
        cta: `Drop ${match[1].replace(/_/g, " ")}`,
      };
    }
  }

  if (suggestion.constraint === "electrical") {
    return {
      body: { relaxation: "confirm_electrical" },
      cta: "Confirm power is available",
    };
  }

  return null;
}

export function ConflictPanel({ conflict, brief, onResolve, busy }: Props) {
  const [customBudget, setCustomBudget] = useState("");

  const actionable = conflict.possible_relaxations
    .map((suggestion) => ({ suggestion, action: actionFor(suggestion, brief) }))
    .filter((item) => item.action !== null);

  // Deduplicate: several suggestions can map to the same concrete action.
  const seen = new Set<string>();
  const choices = actionable.filter((item) => {
    const key = JSON.stringify(item.action!.body);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return (
    <section className="panel conflict">
      <h2>These requirements cannot all be met</h2>
      <p className="lead">
        No configuration in the catalog satisfies every constraint you set. Nothing has
        been substituted quietly — here is exactly what blocked it, and what you can
        change.
      </p>

      <h3>What blocked it</h3>
      <ul className="violations">
        {conflict.violated_constraints.map((violation) => (
          <li key={`${violation.constraint}-${violation.status}`}>
            <strong>{CONSTRAINT_NAMES[violation.constraint] ?? violation.constraint}</strong>
            <span className={violation.status === "fail" ? "badge badge-bad" : "badge badge-warn"}>
              {violation.status === "fail" ? "blocked" : "needs verification"}
            </span>
            <p>{violation.example_reasons[0]}</p>
          </li>
        ))}
      </ul>

      {conflict.closest_alternatives.length > 0 && (
        <>
          <h3>Closest we could get</h3>
          <ul className="closest">
            {conflict.closest_alternatives.slice(0, 2).map((alternative, index) => (
              <li key={index}>
                <strong>{formatMoney(alternative.total_price, alternative.currency)}</strong>{" "}
                — {alternative.products.map((p) => p.category.replace(/_/g, " ")).join(", ")}
                <span className="muted">
                  {" "}
                  ({alternative.violations.filter((v) => v.blocking).length} blocking issue(s))
                </span>
              </li>
            ))}
          </ul>
        </>
      )}

      <h3>Choose what gives way</h3>
      <p className="hint">
        The system will not decide this for you. Pick one and the entire plan is
        recomputed from scratch.
      </p>

      <div className="choices">
        {choices.map(({ suggestion, action }) => (
          <button
            key={action!.cta}
            className="choice"
            disabled={busy}
            onClick={() => onResolve(action!.body)}
          >
            <span className="choice-cta">{action!.cta}</span>
            <span className="choice-why">{suggestion.description}</span>
          </button>
        ))}

        <div className="choice choice-custom">
          <span className="choice-cta">Set your own budget</span>
          <div className="custom-row">
            <input
              type="number"
              placeholder={brief.budget ? String(brief.budget) : "Budget"}
              value={customBudget}
              onChange={(e) => setCustomBudget(e.target.value)}
            />
            <button
              disabled={busy || !customBudget}
              onClick={() =>
                onResolve({ relaxation: "increase_budget", budget: Number(customBudget) })
              }
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {conflict.possible_relaxations.length > choices.length && (
        <details className="other-options">
          <summary>Other changes that would help</summary>
          <ul>
            {conflict.possible_relaxations.map((suggestion) => (
              <li key={suggestion.description}>{suggestion.description}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
