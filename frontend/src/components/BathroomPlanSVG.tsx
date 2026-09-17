import type { RoomLayout } from "../types";

/**
 * Renders the layout solver's actual output.
 *
 * Nothing here is decorative: every rectangle is a coordinate the solver
 * computed, and the dashed clearance zones are the code-required clear floor
 * that determined whether the configuration was feasible at all. Showing them
 * is the point — it makes the constraint visible rather than asking the user to
 * trust a verdict.
 */

const PADDING = 44;
const CATEGORY_COLOURS: Record<string, string> = {
  toilet: "#2f6f8f",
  smart_toilet: "#1f5d7a",
  vanity: "#7a5b3a",
  basin: "#8a6a47",
  shower: "#3f7d6a",
  smart_shower: "#2f6d5a",
  bathtub: "#4a6f9c",
  storage: "#6b6b7d",
};

const label = (category: string) => category.replace(/_/g, " ");

export function BathroomPlanSVG({ layout }: { layout: RoomLayout }) {
  if (!layout.room_width_in || !layout.room_length_in) {
    return (
      <div className="plan-empty">
        No room dimensions were supplied, so no plan could be solved.
      </div>
    );
  }

  const roomW = layout.room_width_in;
  const roomL = layout.room_length_in;
  // Fit the room into a fixed drawing box, preserving aspect ratio.
  const maxDim = Math.max(roomW, roomL);
  const scale = 380 / maxDim;
  const w = roomW * scale;
  const h = roomL * scale;

  // SVG y grows downward; room y grows upward. Flip so the plan reads naturally.
  const fy = (yIn: number, depthIn: number) => PADDING + (roomL - yIn - depthIn) * scale;
  const fx = (xIn: number) => PADDING + xIn * scale;

  return (
    <div className="plan-wrap">
      <svg
        viewBox={`0 0 ${w + PADDING * 2} ${h + PADDING * 2}`}
        className="plan-svg"
        role="img"
        aria-label="Conceptual bathroom plan"
      >
        <rect
          x={PADDING}
          y={PADDING}
          width={w}
          height={h}
          className="plan-room"
        />

        {/* Clearance zones first, so fixtures draw on top of them. */}
        {layout.placed.map((item) => (
          <rect
            key={`c-${item.product_id}`}
            x={fx(item.clearance.x_in)}
            y={fy(item.clearance.y_in, item.clearance.depth_in)}
            width={item.clearance.width_in * scale}
            height={item.clearance.depth_in * scale}
            className="plan-clearance"
          >
            <title>{`Required clear space — ${item.clearance_source}`}</title>
          </rect>
        ))}

        {layout.door_swing && (
          <rect
            x={fx(layout.door_swing.x_in)}
            y={fy(layout.door_swing.y_in, layout.door_swing.depth_in)}
            width={layout.door_swing.width_in * scale}
            height={layout.door_swing.depth_in * scale}
            className="plan-door-swing"
          >
            <title>Door swing — this floor area must stay clear</title>
          </rect>
        )}

        {layout.placed.map((item) => {
          const x = fx(item.footprint.x_in);
          const y = fy(item.footprint.y_in, item.footprint.depth_in);
          const fw = item.footprint.width_in * scale;
          const fh = item.footprint.depth_in * scale;
          const colour = CATEGORY_COLOURS[item.category] ?? "#555";
          return (
            <g key={item.product_id}>
              <rect x={x} y={y} width={fw} height={fh} fill={colour} rx={3} />
              <title>
                {`${item.product_name}\n${item.footprint.width_in}in x ${item.footprint.depth_in}in on the ${item.wall} wall`}
              </title>
              {fw > 34 && fh > 16 && (
                <text x={x + fw / 2} y={y + fh / 2 + 4} className="plan-fixture-label">
                  {label(item.category)}
                </text>
              )}
            </g>
          );
        })}

        {/* Dimension annotations */}
        <text x={PADDING + w / 2} y={PADDING - 16} className="plan-dim">
          {(roomW / 12).toFixed(1)} ft
        </text>
        <text
          x={PADDING - 16}
          y={PADDING + h / 2}
          className="plan-dim"
          transform={`rotate(-90 ${PADDING - 16} ${PADDING + h / 2})`}
        >
          {(roomL / 12).toFixed(1)} ft
        </text>
      </svg>

      <div className="plan-legend">
        <span className="legend-item">
          <span className="swatch swatch-fixture" /> Fixture footprint
        </span>
        <span className="legend-item">
          <span className="swatch swatch-clearance" /> Required clear space (code minimum)
        </span>
        {layout.door_swing && (
          <span className="legend-item">
            <span className="swatch swatch-door" /> Door swing
          </span>
        )}
      </div>

      <p className="plan-caption">
        <strong>Conceptual planning view.</strong> Positions are computed from your stated
        dimensions and published clearance minimums. This is not an installation drawing —
        final dimensions, plumbing, electrical and local-code requirements must be verified
        by a qualified professional.
      </p>

      {layout.unplaced.length > 0 && (
        <ul className="plan-unplaced">
          {layout.unplaced.map((item) => (
            <li key={item.product_id}>
              <strong>{item.product_name}</strong> could not be placed — {item.reason}
            </li>
          ))}
        </ul>
      )}
      {!layout.circulation_ok &&
        layout.circulation_notes.map((note) => (
          <p key={note} className="plan-warning">
            {note}
          </p>
        ))}
    </div>
  );
}
