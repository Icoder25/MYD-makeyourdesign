import { useState } from "react";
import type { PlanRequest } from "../api";

const ALL_CATEGORIES = [
  "vanity",
  "basin",
  "faucet",
  "toilet",
  "smart_toilet",
  "shower",
  "smart_shower",
  "bathtub",
  "storage",
];

const STYLES = ["modern", "minimalist", "contemporary", "transitional", "traditional", "luxury"];

const PRIORITIES = [
  { id: "water_efficiency", label: "Water efficiency" },
  { id: "smart_features", label: "Smart features" },
  { id: "storage", label: "Storage" },
  { id: "budget", label: "Keeping cost down" },
] as const;

type Priority = (typeof PRIORITIES)[number]["id"];

export const GOLDEN_PATH: Partial<State> = {
  width: "6",
  length: "8",
  budget: "250000",
  categories: ["vanity", "basin", "faucet", "toilet", "shower"],
  styles: ["modern", "minimalist"],
  priorities: ["water_efficiency", "smart_features"],
  household: "3",
  electrical: "unknown",
};

interface State {
  width: string;
  length: string;
  budget: string;
  categories: string[];
  styles: string[];
  priorities: Priority[];
  household: string;
  electrical: "yes" | "no" | "unknown";
  roughIn: string;
  doorWall: string;
  doorSwing: string;
}

const INITIAL: State = {
  width: "6",
  length: "8",
  budget: "250000",
  categories: ["vanity", "basin", "faucet", "toilet", "shower"],
  styles: ["modern", "minimalist"],
  priorities: ["water_efficiency"],
  household: "3",
  electrical: "unknown",
  roughIn: "",
  doorWall: "south",
  doorSwing: "inward",
};

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

export function buildRequest(state: State): PlanRequest {
  const weights: Record<string, number> = {
    spatial: 1,
    budget: 1,
    preference: 1,
    water_efficiency: 1,
    style: 1,
    smart_feature: 1,
  };
  for (const priority of state.priorities) {
    if (priority === "water_efficiency") weights.water_efficiency = 4;
    if (priority === "smart_features") weights.smart_feature = 4;
    if (priority === "storage") weights.preference = 3;
    if (priority === "budget") weights.budget = 3;
  }

  return {
    room_width_ft: state.width ? Number(state.width) : null,
    room_length_ft: state.length ? Number(state.length) : null,
    budget: state.budget ? Number(state.budget) : null,
    required_categories: state.categories,
    preferred_styles: state.styles,
    electrical_available:
      state.electrical === "unknown" ? null : state.electrical === "yes",
    toilet_rough_in_in: state.roughIn ? Number(state.roughIn) : null,
    door: { wall: state.doorWall, offset_in: 6, width_in: 30, swing: state.doorSwing },
    preferences: {
      preferred_styles: state.styles,
      smart_feature_preference: state.priorities.includes("smart_features")
        ? "prefer"
        : "neutral",
      storage_preference: state.priorities.includes("storage") ? "spacious" : "neutral",
    },
    weights,
    usage: {
      household_size: Number(state.household) || 3,
      flushes_per_person_per_day: 4,
      shower_minutes_per_person_per_day: 4.8,
      faucet_minutes_per_person_per_day: 2,
    },
  };
}

interface Props {
  onSubmit: (request: PlanRequest) => void;
  onImageSelected: (file: File) => void;
  busy: boolean;
  visionAvailable: boolean;
  imageName: string | null;
}

export function BriefForm({ onSubmit, onImageSelected, busy, visionAvailable, imageName }: Props) {
  const [state, setState] = useState<State>(INITIAL);
  const set = <K extends keyof State>(key: K, value: State[K]) =>
    setState((prev) => ({ ...prev, [key]: value }));

  const dimensionsMissing = !state.width || !state.length;

  return (
    <form
      className="panel"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(buildRequest(state));
      }}
    >
      <h2>1 · Your bathroom</h2>

      <div className="field-row">
        <label>
          Width (ft)
          <input
            type="number"
            min="2"
            max="60"
            step="0.5"
            value={state.width}
            onChange={(e) => set("width", e.target.value)}
          />
        </label>
        <label>
          Length (ft)
          <input
            type="number"
            min="2"
            max="60"
            step="0.5"
            value={state.length}
            onChange={(e) => set("length", e.target.value)}
          />
        </label>
        <label>
          Budget (₹)
          <input
            type="number"
            min="0"
            step="5000"
            value={state.budget}
            onChange={(e) => set("budget", e.target.value)}
          />
        </label>
      </div>

      {dimensionsMissing && (
        <p className="inline-note">
          Without dimensions no layout can be solved, so spatial feasibility will stay
          unverified.
        </p>
      )}

      <label className="upload">
        <span>Bathroom photo (optional)</span>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onImageSelected(file);
          }}
        />
        <span className="hint">
          {imageName ? (
            <strong style={{ color: "var(--accent)" }}>Selected: {imageName}</strong>
          ) : visionAvailable ? (
            "A photo adds advisory visual context. It can never establish a dimension or a rough-in."
          ) : (
            "Attach site photo for architectural visual reference. (AI vision analysis requires GEMINI_API_KEY)."
          )}
        </span>
      </label>

      <h3>Fixtures you need</h3>
      <div className="chips">
        {ALL_CATEGORIES.map((category) => (
          <button
            key={category}
            type="button"
            className={state.categories.includes(category) ? "chip chip-on" : "chip"}
            onClick={() => set("categories", toggle(state.categories, category))}
          >
            {category.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <h3>Style</h3>
      <div className="chips">
        {STYLES.map((style) => (
          <button
            key={style}
            type="button"
            className={state.styles.includes(style) ? "chip chip-on" : "chip"}
            onClick={() => set("styles", toggle(state.styles, style))}
          >
            {style}
          </button>
        ))}
      </div>

      <h3>What matters most</h3>
      <div className="chips">
        {PRIORITIES.map((priority) => (
          <button
            key={priority.id}
            type="button"
            className={state.priorities.includes(priority.id) ? "chip chip-on" : "chip"}
            onClick={() => set("priorities", toggle(state.priorities, priority.id))}
          >
            {priority.label}
          </button>
        ))}
      </div>

      <h3>What you can confirm</h3>
      <p className="hint">
        Leave these unknown if you have not measured them. Unknown stays unknown — it
        becomes a verification step on the result, never a silent assumption.
      </p>
      <div className="field-row">
        <label>
          Power at the fixture location
          <select
            value={state.electrical}
            onChange={(e) => set("electrical", e.target.value as State["electrical"])}
          >
            <option value="unknown">Not sure yet</option>
            <option value="yes">Confirmed available</option>
            <option value="no">Confirmed unavailable</option>
          </select>
        </label>
        <label>
          Toilet rough-in (in)
          <input
            type="number"
            min="1"
            step="0.5"
            placeholder="Not measured"
            value={state.roughIn}
            onChange={(e) => set("roughIn", e.target.value)}
          />
        </label>
        <label>
          Household size
          <input
            type="number"
            min="1"
            max="12"
            value={state.household}
            onChange={(e) => set("household", e.target.value)}
          />
        </label>
      </div>

      <div className="field-row">
        <label>
          Door wall
          <select value={state.doorWall} onChange={(e) => set("doorWall", e.target.value)}>
            {["south", "north", "west", "east"].map((wall) => (
              <option key={wall} value={wall}>
                {wall}
              </option>
            ))}
          </select>
        </label>
        <label>
          Door opens
          <select value={state.doorSwing} onChange={(e) => set("doorSwing", e.target.value)}>
            <option value="inward">Inward (consumes floor)</option>
            <option value="outward">Outward</option>
            <option value="sliding">Sliding</option>
          </select>
        </label>
      </div>

      <div className="actions">
        <button type="submit" className="primary" disabled={busy}>
          {busy ? "Planning…" : "Generate plan"}
        </button>
        <button
          type="button"
          className="ghost"
          onClick={() => setState({ ...INITIAL, ...GOLDEN_PATH } as State)}
        >
          Reset to demo brief
        </button>
      </div>
    </form>
  );
}
