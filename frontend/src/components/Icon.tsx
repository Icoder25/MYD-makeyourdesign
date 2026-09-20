import React from "react";

/**
 * One drawn icon set for the whole studio.
 *
 * Emoji were doing this job before. They are a different typeface on every
 * machine, they carry colour we did not choose, and they read as a chat window
 * rather than a set of drawings — so they are replaced here by stroked glyphs
 * on a single 16-unit grid, all at the same weight, all inheriting
 * `currentColor` so a glyph is always the colour of the text beside it.
 */

export type IconName =
  | "plan"
  | "folder"
  | "spark"
  | "box"
  | "pulse"
  | "drop"
  | "doc"
  | "lock"
  | "check"
  | "warn"
  | "cross"
  | "close"
  | "toilet"
  | "shower"
  | "bath"
  | "basin"
  | "mirror"
  | "vanity"
  | "wrench"
  | "clipboard"
  | "money"
  | "link"
  | "palette"
  | "studio"
  | "refresh"
  | "eye"
  | "door"
  | "archive"
  | "phone"
  | "layers"
  | "expand"
  | "mouse"
  | "keyboard"
  | "camera"
  | "trash"
  | "ruler"
  | "plug"
  | "sun"
  | "moon"
  | "monitor"
  | "caretUp"
  | "caretDown"
  | "arrowRight"
  | "external"
  | "plus"
  | "minus"
  | "search"
  | "leaf"
  | "compass"
  | "seal"
  | "dot";

/** Stroked paths. Anything that needs a solid counts as `FILLED` below. */
const PATHS: Record<IconName, React.ReactNode> = {
  plan: (
    <>
      <path d="M2.5 13.5 13.5 2.5v11z" />
      <path d="M5.6 12.4h2M8.6 9.4v2" />
    </>
  ),
  folder: (
    <>
      <path d="M1.8 4.2h4.1l1.3 1.6h7v6.4a1 1 0 0 1-1 1H2.8a1 1 0 0 1-1-1z" />
      <path d="M4.4 4.2V2.9h6.9v2.9" />
    </>
  ),
  spark: (
    <>
      <path d="M8 1.6 9.5 6 14 7.5 9.5 9 8 13.4 6.5 9 2 7.5 6.5 6z" />
      <path d="M12.6 11.4v2.6M11.3 12.7h2.6" />
    </>
  ),
  box: (
    <>
      <path d="M8 1.8 14.2 5v6L8 14.2 1.8 11V5z" />
      <path d="M1.8 5 8 8.2 14.2 5M8 8.2v6" />
    </>
  ),
  pulse: <path d="M1.6 8.3h3.1l1.9-4.6 2.7 8.6 1.8-4h3.3" />,
  drop: <path d="M8 1.8s4.3 4.4 4.3 7.3a4.3 4.3 0 0 1-8.6 0C3.7 6.2 8 1.8 8 1.8Z" />,
  doc: (
    <>
      <path d="M3.6 1.8h5.3l3.5 3.5v8.9H3.6z" />
      <path d="M8.9 1.8v3.5h3.5M5.9 8.4h4.2M5.9 10.8h4.2" />
    </>
  ),
  lock: (
    <>
      <rect x="3.2" y="7" width="9.6" height="7.1" rx="1.1" />
      <path d="M5.5 7V4.9a2.5 2.5 0 0 1 5 0V7" />
    </>
  ),
  check: <path d="M2.8 8.6 6.2 12 13.2 4.4" />,
  warn: (
    <>
      <path d="M8 2.2 15 13.8H1z" />
      <path d="M8 6.6v3.2M8 11.8v.1" />
    </>
  ),
  cross: <path d="M4 4l8 8M12 4l-8 8" />,
  close: <path d="M3.8 3.8l8.4 8.4M12.2 3.8l-8.4 8.4" />,
  toilet: (
    <>
      <path d="M4 2.2h1.9v4.4H4z" />
      <path d="M2.6 6.6h10.2v1.6a5.1 5.1 0 0 1-5.1 5.1 5.1 5.1 0 0 1-5.1-5.1z" />
      <path d="M5.6 13.3v1.1h4.8v-1.1" />
    </>
  ),
  shower: (
    <>
      <path d="M2.4 13.6V5.4a2.8 2.8 0 0 1 5.6 0" />
      <path d="M8 3.4h5.6M10.4 3.4v1.8" />
      <path d="M9.2 7.4v1.4M11.6 7.4v1.4M13.9 7.4v1.4M10.4 10.6V12M12.8 10.6V12" />
    </>
  ),
  bath: (
    <>
      <path d="M1.6 7.8h12.8v2.3a3 3 0 0 1-3 3H4.6a3 3 0 0 1-3-3z" />
      <path d="M3.4 7.8V3.6a1.6 1.6 0 0 1 3.2 0" />
      <path d="M3.9 13.1v1.2M12.1 13.1v1.2" />
    </>
  ),
  basin: (
    <>
      <path d="M2 8.6h12v1.4a3.4 3.4 0 0 1-3.4 3.4H5.4A3.4 3.4 0 0 1 2 10z" />
      <path d="M8 8.6V4.8a2.2 2.2 0 0 1 2.2-2.2h1.6" />
    </>
  ),
  mirror: (
    <>
      <ellipse cx="8" cy="6.6" rx="4.3" ry="5" />
      <path d="M8 11.6v2.6M5.7 14.2h4.6" />
    </>
  ),
  vanity: (
    <>
      <path d="M1.8 5.4h12.4v3H1.8z" />
      <path d="M3.4 8.4v5.2M12.6 8.4v5.2M8 8.4v5.2" />
    </>
  ),
  wrench: (
    <path d="M10.2 1.9a3.9 3.9 0 0 0-3.4 5.8l-5 5 1.6 1.6 5-5a3.9 3.9 0 0 0 5.1-4.9l-2.3 2.3-2-.5-.5-2z" />
  ),
  clipboard: (
    <>
      <path d="M5.4 3h-1a1 1 0 0 0-1 1v9.3a1 1 0 0 0 1 1h7.2a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1h-1" />
      <rect x="5.4" y="1.7" width="5.2" height="2.6" rx=".7" />
      <path d="M6 8.2h4M6 10.7h4" />
    </>
  ),
  money: (
    <>
      <rect x="1.6" y="4" width="12.8" height="8" rx="1.2" />
      <circle cx="8" cy="8" r="2" />
      <path d="M4.3 8h.1M11.6 8h.1" />
    </>
  ),
  link: (
    <>
      <path d="M6.7 9.3a2.6 2.6 0 0 0 3.9.3l2-2a2.6 2.6 0 0 0-3.7-3.7l-1.1 1.1" />
      <path d="M9.3 6.7a2.6 2.6 0 0 0-3.9-.3l-2 2a2.6 2.6 0 0 0 3.7 3.7l1.1-1.1" />
    </>
  ),
  palette: (
    <>
      <path d="M8 1.8a6.2 6.2 0 0 0 0 12.4c.9 0 1.4-.6 1.4-1.3 0-.8-.6-1.2-.6-1.8 0-.6.5-1 1.1-1h1.4a2.9 2.9 0 0 0 2.9-2.9C14.2 4 11.4 1.8 8 1.8Z" />
      <path d="M4.9 7.1h.1M7.2 5h.1M10 5.4h.1" />
    </>
  ),
  studio: (
    <>
      <path d="M1.8 6.2 8 2.2l6.2 4" />
      <path d="M3.4 6.9v6.1M6.4 6.9v6.1M9.6 6.9v6.1M12.6 6.9v6.1" />
      <path d="M1.8 13.6h12.4" />
    </>
  ),
  refresh: (
    <>
      <path d="M13.4 7.2a5.5 5.5 0 0 0-9.6-2.6L2.2 6" />
      <path d="M2.6 8.8a5.5 5.5 0 0 0 9.6 2.6l1.6-1.4" />
      <path d="M2.2 2.8V6h3.2M13.8 13.2V10h-3.2" />
    </>
  ),
  eye: (
    <>
      <path d="M.9 8S3.6 3.4 8 3.4 15.1 8 15.1 8 12.4 12.6 8 12.6.9 8 .9 8Z" />
      <circle cx="8" cy="8" r="2.1" />
    </>
  ),
  door: (
    <>
      <path d="M4 1.9h8v12.2H4z" />
      <path d="M2.4 14.1h11.2M9.7 8.2v.1" />
    </>
  ),
  archive: (
    <>
      <rect x="1.8" y="2.4" width="12.4" height="3.4" rx=".8" />
      <path d="M3 5.8v6.9a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5.8" />
      <path d="M6.4 8.8h3.2" />
    </>
  ),
  phone: (
    <>
      <rect x="4.2" y="1.6" width="7.6" height="12.8" rx="1.4" />
      <path d="M7 3.4h2M8 12.2v.1" />
    </>
  ),
  layers: (
    <>
      <path d="M8 1.9 14.4 5.4 8 8.9 1.6 5.4z" />
      <path d="M1.6 8.6 8 12.1l6.4-3.5" />
    </>
  ),
  expand: <path d="M6 1.9H1.9V6M10 1.9h4.1V6M10 14.1h4.1V10M6 14.1H1.9V10" />,
  mouse: (
    <>
      <rect x="4.4" y="1.7" width="7.2" height="12.6" rx="3.6" />
      <path d="M8 4.4v2.4" />
    </>
  ),
  keyboard: (
    <>
      <rect x="1" y="4" width="14" height="8" rx="1.2" />
      <path d="M3.6 6.6h.1M6.2 6.6h.1M8.8 6.6h.1M11.4 6.6h.1M5 9.4h6" />
    </>
  ),
  camera: (
    <>
      <path d="M1.7 5.4h2.6l1.2-1.8h4.6l1.2 1.8h2.6a.9.9 0 0 1 .9.9v6a.9.9 0 0 1-.9.9H1.7a.9.9 0 0 1-.9-.9v-6a.9.9 0 0 1 .9-.9Z" />
      <circle cx="8" cy="9.3" r="2.4" />
    </>
  ),
  trash: (
    <>
      <path d="M2.4 4.2h11.2" />
      <path d="M3.9 4.2 4.6 14a.9.9 0 0 0 .9.8h5a.9.9 0 0 0 .9-.8l.7-9.8" />
      <path d="M6.2 4.2V2.6a.8.8 0 0 1 .8-.8h2a.8.8 0 0 1 .8.8v1.6M6.8 7v4.7M9.2 7v4.7" />
    </>
  ),
  ruler: (
    <>
      <rect x="1" y="5.2" width="14" height="5.6" rx=".8" />
      <path d="M4 5.2v2.1M6.4 5.2v3.1M8.8 5.2v2.1M11.2 5.2v3.1" />
    </>
  ),
  plug: (
    <>
      <path d="M5.4 1.9v3.6M10.6 1.9v3.6" />
      <path d="M3.6 5.5h8.8v2.1a4.4 4.4 0 0 1-8.8 0z" />
      <path d="M8 12v2.2" />
    </>
  ),
  sun: (
    <>
      <circle cx="8" cy="8" r="3.1" />
      <path d="M8 1.2v1.6M8 13.2v1.6M1.2 8h1.6M13.2 8h1.6M3.2 3.2l1.1 1.1M11.7 11.7l1.1 1.1M12.8 3.2l-1.1 1.1M4.3 11.7l-1.1 1.1" />
    </>
  ),
  moon: <path d="M13.2 9.6A5.8 5.8 0 0 1 6.4 2.8a5.8 5.8 0 1 0 6.8 6.8Z" />,
  monitor: (
    <>
      <rect x="1.4" y="2.6" width="13.2" height="8.6" rx="1.1" />
      <path d="M5.6 14.2h4.8M8 11.2v3" />
    </>
  ),
  caretUp: <path d="M4.2 9.8 8 6l3.8 3.8" />,
  caretDown: <path d="M4.2 6.2 8 10l3.8-3.8" />,
  arrowRight: <path d="M2.6 8h10.4M9.2 4.2 13 8l-3.8 3.8" />,
  external: <path d="M9.6 2.6h3.8v3.8M13.4 2.6 7.8 8.2M12 9.6v3a.8.8 0 0 1-.8.8H3.4a.8.8 0 0 1-.8-.8V4.8a.8.8 0 0 1 .8-.8h3" />,
  plus: <path d="M8 3.2v9.6M3.2 8h9.6" />,
  minus: <path d="M3.2 8h9.6" />,
  search: (
    <>
      <circle cx="7.1" cy="7.1" r="4.6" />
      <path d="M10.5 10.5 14 14" />
    </>
  ),
  leaf: (
    <>
      <path d="M13.6 2.4C6.9 2 2.4 4.7 2.4 9a4.6 4.6 0 0 0 4.6 4.6c4.3 0 6.9-4.5 6.6-11.2Z" />
      <path d="M3.4 13.6c2-4.3 4.7-7 8.2-8.8" />
    </>
  ),
  compass: (
    <>
      <circle cx="8" cy="8" r="6.2" />
      <path d="M10.6 5.4 9.2 9.2 5.4 10.6 6.8 6.8z" />
    </>
  ),
  seal: (
    <>
      <circle cx="8" cy="7" r="4.4" />
      <path d="M5.6 10.8 4.8 14.6 8 13.1l3.2 1.5-.8-3.8" />
    </>
  ),
  dot: <circle cx="8" cy="8" r="3" />,
};

/** Glyphs that read better solid than stroked. */
const FILLED = new Set<IconName>(["dot", "moon", "drop"]);

interface IconProps {
  name: IconName;
  /** Rendered size in px. The stroke compensates so weight stays even. */
  size?: number;
  className?: string;
  /** Supply when the icon is the only content of a control. */
  title?: string;
}

export const Icon: React.FC<IconProps> = ({ name, size = 16, className, title }) => {
  const filled = FILLED.has(name);
  return (
    <svg
      viewBox="0 0 16 16"
      width={size}
      height={size}
      className={`ui-icon${className ? ` ${className}` : ""}`}
      fill={filled ? "currentColor" : "none"}
      stroke={filled ? "none" : "currentColor"}
      strokeWidth={filled ? 0 : (1.3 * 16) / size + 0.15}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
      focusable="false"
    >
      {title ? <title>{title}</title> : null}
      {PATHS[name]}
    </svg>
  );
};

/** Product categories map onto the drawn set, so the schedule, the inspector
 *  and the dock all show the same mark for the same thing. */
export const CATEGORY_ICON: Record<string, IconName> = {
  toilet: "toilet",
  smart_toilet: "toilet",
  shower: "shower",
  smart_shower: "shower",
  bathtub: "bath",
  basin: "basin",
  vanity: "vanity",
  mirror: "mirror",
  storage: "archive",
  faucet: "basin",
  lighting: "spark",
};

export const categoryIcon = (category: string): IconName =>
  CATEGORY_ICON[category] ?? "box";
