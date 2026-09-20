import React from "react";
import type { RoomLayout } from "../types";

/**
 * Renders the layout solver's actual output.
 *
 * Every rectangle is a coordinate the solver computed, and dashed clearance
 * zones are code-required clear floors. Fixture hover highlights synchronize
 * with the product schedule and inspector.
 */

const PADDING = 58;

/**
 * Plan drawings separate fixtures by tone and material, not by hue. A drafting
 * sheet that runs through the full spectrum reads as a chart; a tight warm
 * range — graphite, walnut, soapstone, stone — reads as a room.
 */
const CATEGORY_COLOURS: Record<string, string> = {
  toilet: "#4a555b",
  smart_toilet: "#3c4a51",
  vanity: "#6d583f",
  basin: "#836d4e",
  shower: "#4d5c58",
  smart_shower: "#3f504c",
  bathtub: "#46535d",
  storage: "#57524a",
  mirror: "#6b6a64",
};

const FALLBACK_COLOUR = "#5a564f";

const label = (category: string) => category.replace(/_/g, " ");

/** Feet-and-inches, the way a drawing is actually annotated. */
const feetInches = (inches: number) => {
  const ft = Math.floor(inches / 12);
  const inch = Math.round(inches - ft * 12);
  return inch === 0 ? `${ft}′-0″` : `${ft}′-${inch}″`;
};

interface BathroomPlanSVGProps {
  layout: RoomLayout;
  highlightedProductId?: string | null;
  selectedProductId?: string | null;
  onSelectProduct?: (productId: string) => void;
  showGrid?: boolean;
  zoomScale?: number;
}

export const BathroomPlanSVG: React.FC<BathroomPlanSVGProps> = ({
  layout,
  highlightedProductId,
  selectedProductId,
  onSelectProduct,
  showGrid = true,
  zoomScale = 1.0,
}) => {
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
  const scale = (380 / maxDim) * zoomScale;
  const w = roomW * scale;
  const h = roomL * scale;

  // SVG y grows downward; room y grows upward. Flip so the plan reads naturally.
  const fy = (yIn: number, depthIn: number) => PADDING + (roomL - yIn - depthIn) * scale;
  const fx = (xIn: number) => PADDING + xIn * scale;

  // Where the dimension strings sit, clear of the wall poché.
  const dimTop = PADDING - 30;
  const dimLeft = PADDING - 30;

  // Generate 12-inch grid coordinates
  const gridLinesX: number[] = [];
  for (let gx = 12; gx < roomW; gx += 12) {
    gridLinesX.push(gx);
  }
  const gridLinesY: number[] = [];
  for (let gy = 12; gy < roomL; gy += 12) {
    gridLinesY.push(gy);
  }

  return (
    <div className="plan-wrap">
      <svg
        viewBox={`0 0 ${w + PADDING * 2} ${h + PADDING * 2}`}
        className="plan-svg"
        role="img"
        aria-label="Architectural 2D bathroom layout plan"
      >
        <defs>
          <filter id="glow-highlight" x="-25%" y="-25%" width="150%" height="150%">
            <feDropShadow
              dx="0"
              dy="0"
              stdDeviation="5"
              floodColor="var(--brass)"
              floodOpacity="0.85"
            />
          </filter>
          {/* Wall poché: the hatch that tells you a wall is solid. */}
          <pattern
            id="wall-poche"
            width="5"
            height="5"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <line x1="0" y1="0" x2="0" y2="5" className="plan-poche-line" />
          </pattern>
        </defs>

        {/* Wall thickness, drawn as poché outside the clear opening */}
        <rect
          x={PADDING - 7}
          y={PADDING - 7}
          width={w + 14}
          height={h + 14}
          className="plan-wall-band"
          fill="url(#wall-poche)"
        />

        {/* Room boundary */}
        <rect
          x={PADDING}
          y={PADDING}
          width={w}
          height={h}
          className="plan-room"
        />

        {/* 12-inch Architectural Grid */}
        {showGrid && (
          <g className="plan-grid-lines">
            {gridLinesX.map((gx) => (
              <line
                key={`gx-${gx}`}
                x1={fx(gx)}
                y1={PADDING}
                x2={fx(gx)}
                y2={PADDING + h}
                stroke="var(--canvas-grid)"
                strokeWidth={0.7}
                strokeDasharray="2,3"
              />
            ))}
            {gridLinesY.map((gy) => (
              <line
                key={`gy-${gy}`}
                x1={PADDING}
                y1={fy(gy, 0)}
                x2={PADDING + w}
                y2={fy(gy, 0)}
                stroke="var(--canvas-grid)"
                strokeWidth={0.7}
                strokeDasharray="2,3"
              />
            ))}
          </g>
        )}

        {/* Clearance zones first, so fixtures draw on top of them */}
        {layout.placed.map((item) => {
          const isItemActive =
            highlightedProductId === item.product_id ||
            selectedProductId === item.product_id;

          return (
            <rect
              key={`c-${item.product_id}`}
              x={fx(item.clearance.x_in)}
              y={fy(item.clearance.y_in, item.clearance.depth_in)}
              width={item.clearance.width_in * scale}
              height={item.clearance.depth_in * scale}
              className={`plan-clearance ${isItemActive ? "active-clearance" : ""}`}
            >
              <title>{`Required clear space — ${item.clearance_source}`}</title>
            </rect>
          );
        })}

        {/* Door swing envelope */}
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

        {/* Placed Fixtures */}
        {layout.placed.map((item) => {
          const x = fx(item.footprint.x_in);
          const y = fy(item.footprint.y_in, item.footprint.depth_in);
          const fw = item.footprint.width_in * scale;
          const fh = item.footprint.depth_in * scale;
          const colour = CATEGORY_COLOURS[item.category] ?? FALLBACK_COLOUR;
          const isHighlighted = highlightedProductId === item.product_id;
          const isSelected = selectedProductId === item.product_id;
          const isTargeted = isHighlighted || isSelected;

          return (
            <g
              key={item.product_id}
              className={`plan-fixture-group ${isTargeted ? "targeted" : ""}`}
              onClick={() => onSelectProduct && onSelectProduct(item.product_id)}
              style={{ cursor: onSelectProduct ? "pointer" : "default" }}
            >
              <rect
                x={x}
                y={y}
                width={fw}
                height={fh}
                fill={colour}
                rx={2}
                filter={isTargeted ? "url(#glow-highlight)" : undefined}
                stroke={isTargeted ? "var(--brass-bright)" : "rgba(0, 0, 0, 0.18)"}
                strokeWidth={isTargeted ? 2 : 0.8}
              />
              <title>
                {`${item.product_name}\n${item.footprint.width_in}in x ${item.footprint.depth_in}in on the ${item.wall} wall`}
              </title>
              {fw > 34 && fh > 16 && (
                <text
                  x={x + fw / 2}
                  y={y + fh / 2 + 4}
                  className={`plan-fixture-label ${isTargeted ? "label-bold" : ""}`}
                >
                  {label(item.category)}
                </text>
              )}
            </g>
          );
        })}

        {/* Dimension strings — extension lines, witness ticks, then the number,
            the way a set of drawings carries a measurement. */}
        <g className="plan-dim-group">
          {/* Overall width, above the plan */}
          <line x1={PADDING} y1={PADDING - 10} x2={PADDING} y2={dimTop - 5} className="plan-ext-line" />
          <line
            x1={PADDING + w}
            y1={PADDING - 10}
            x2={PADDING + w}
            y2={dimTop - 5}
            className="plan-ext-line"
          />
          <line x1={PADDING} y1={dimTop} x2={PADDING + w} y2={dimTop} className="plan-dim-line" />
          <line x1={PADDING - 4} y1={dimTop + 4} x2={PADDING + 4} y2={dimTop - 4} className="plan-dim-tick" />
          <line
            x1={PADDING + w - 4}
            y1={dimTop + 4}
            x2={PADDING + w + 4}
            y2={dimTop - 4}
            className="plan-dim-tick"
          />
          <text x={PADDING + w / 2} y={dimTop - 7} className="plan-dim">
            {feetInches(roomW)}
            <tspan className="plan-dim-metric"> · {Math.round(roomW * 2.54)} cm</tspan>
          </text>

          {/* Overall length, to the left */}
          <line x1={PADDING - 10} y1={PADDING} x2={dimLeft + 5} y2={PADDING} className="plan-ext-line" />
          <line
            x1={PADDING - 10}
            y1={PADDING + h}
            x2={dimLeft + 5}
            y2={PADDING + h}
            className="plan-ext-line"
          />
          <line x1={dimLeft} y1={PADDING} x2={dimLeft} y2={PADDING + h} className="plan-dim-line" />
          <line x1={dimLeft - 4} y1={PADDING + 4} x2={dimLeft + 4} y2={PADDING - 4} className="plan-dim-tick" />
          <line
            x1={dimLeft - 4}
            y1={PADDING + h + 4}
            x2={dimLeft + 4}
            y2={PADDING + h - 4}
            className="plan-dim-tick"
          />
          <text
            x={dimLeft - 7}
            y={PADDING + h / 2}
            className="plan-dim"
            transform={`rotate(-90 ${dimLeft - 7} ${PADDING + h / 2})`}
          >
            {feetInches(roomL)}
            <tspan className="plan-dim-metric"> · {Math.round(roomL * 2.54)} cm</tspan>
          </text>
        </g>

        {/* Graphic scale — one foot, measured off the same projection */}
        <g className="plan-scale-bar">
          <line
            x1={PADDING}
            y1={PADDING + h + 26}
            x2={PADDING + 12 * scale}
            y2={PADDING + h + 26}
            className="plan-dim-line"
          />
          <line x1={PADDING} y1={PADDING + h + 22} x2={PADDING} y2={PADDING + h + 30} className="plan-dim-tick" />
          <line
            x1={PADDING + 12 * scale}
            y1={PADDING + h + 22}
            x2={PADDING + 12 * scale}
            y2={PADDING + h + 30}
            className="plan-dim-tick"
          />
          <text x={PADDING + 12 * scale + 8} y={PADDING + h + 29} className="plan-scale-text">
            1′-0″
          </text>
        </g>

        {/* North mark */}
        <g className="plan-north" transform={`translate(${PADDING + w + 16} ${PADDING + h + 22})`}>
          <line x1="0" y1="10" x2="0" y2="-10" className="plan-north-stem" />
          <path d="M 0 -12 L 4 -3 L 0 -5 L -4 -3 Z" className="plan-north-head" />
          <text x="0" y="22" className="plan-north-label">
            N
          </text>
        </g>
      </svg>

      <div className="plan-legend">
        <span className="legend-item">
          <span className="swatch swatch-fixture" /> Fixture footprint
        </span>
        <span className="legend-item">
          <span className="swatch swatch-clearance" /> Code clear floor
        </span>
        {layout.door_swing && (
          <span className="legend-item">
            <span className="swatch swatch-door" /> Door envelope
          </span>
        )}
      </div>

      <p className="plan-caption">
        <strong>Conceptual spatial planning view.</strong> Positions are computed from your stated
        dimensions and published code clearance minimums. Verified against NKBA / IRC guidelines.
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
};
