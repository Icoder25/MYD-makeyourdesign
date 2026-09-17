import { useState } from "react";
import type { ModifyResponse } from "../types";

const SUGGESTIONS = [
  "Add a smart shower but keep my budget",
  "Make it cheaper",
  "Prioritise water conservation",
  "I want a smart toilet and a bathtub too",
  "Make it more premium",
];

interface Props {
  onSend: (message: string) => void;
  busy: boolean;
  history: ModifyResponse[];
  llmAvailable: boolean;
}

export function ModifyPanel({ onSend, busy, history, llmAvailable }: Props) {
  const [message, setMessage] = useState("");

  const submit = (text: string) => {
    if (!text.trim() || busy) return;
    onSend(text.trim());
    setMessage("");
  };

  return (
    <section className="panel">
      <h2>5 · Change the plan</h2>
      <p className="hint">
        Describe a change in your own words. Your words are turned into a structured
        request, applied deterministically, and the whole plan is recomputed — so a change
        that breaks a constraint comes back as a conflict, not a quiet compromise.
        {!llmAvailable && (
          <>
            {" "}
            <strong>No language model is configured</strong>, so requests are being
            interpreted by the built-in parser.
          </>
        )}
      </p>

      <form
        className="modify-form"
        onSubmit={(event) => {
          event.preventDefault();
          submit(message);
        }}
      >
        <input
          value={message}
          placeholder="e.g. Add a smart shower but keep my budget"
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit" className="primary" disabled={busy || !message.trim()}>
          {busy ? "Recomputing…" : "Apply"}
        </button>
      </form>

      <div className="chips">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            className="chip"
            disabled={busy}
            onClick={() => submit(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>

      {history.length > 0 && (
        <ol className="modify-history">
          {history.map((entry, index) => (
            <li key={index}>
              <p className="understood">
                {entry.understood_as}
                <span className="source-tag">
                  {entry.interpretation_source === "llm" ? "AI interpreted" : "parser interpreted"}
                </span>
              </p>
              <ul>
                {entry.applied_changes.map((change) => (
                  <li key={change}>{change}</li>
                ))}
              </ul>
              <p className={entry.plan.status === "ok" ? "outcome ok" : "outcome conflict"}>
                {entry.plan.status === "ok"
                  ? `→ ${entry.plan.candidates.length} option(s) recomputed`
                  : "→ Conflict: these requirements cannot all hold"}
              </p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
