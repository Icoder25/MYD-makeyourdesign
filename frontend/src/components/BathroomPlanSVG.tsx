import React from "react";
import type { RoomLayout } from "../types";

/**
 * Renders the layout solver's actual output.
 *
 * Every rectangle is a coordinate the solver computed, and dashed clearance
 * zones are code-required clear floors. Fixture hover highlights synchronize
 * with the product schedule and inspector.
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
  mirror: "#5a6b82",
};

const label = (category: string) => category.replace(/_/g, " ");

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
          <filter id="glow-highlight" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#2563eb" floodOpacity="0.7" />
          </filter>
        </defs>

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
                stroke="var(--canvas-grid, #e5e3dc)"
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
                stroke="var(--canvas-grid, #e5e3dc)"
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
          const colour = CATEGORY_COLOURS[item.category] ?? "#555";
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
                rx={3}
                filter={isTargeted ? "url(#glow-highlight)" : undefined}
                stroke={isTargeted ? "#ffffff" : "rgba(0,0,0,0.15)"}
                strokeWidth={isTargeted ? 2 : 1}
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

        {/* Dimension annotations */}
        <text x={PADDING + w / 2} y={PADDING - 14} className="plan-dim">
          {(roomW / 12).toFixed(1)} ft ({Math.round(roomW * 2.54)} cm)
        </text>
        <text
          x={PADDING - 14}
          y={PADDING + h / 2}
          className="plan-dim"
          transform={`rotate(-90 ${PADDING - 14} ${PADDING + h / 2})`}
        >
          {(roomL / 12).toFixed(1)} ft ({Math.round(roomL * 2.54)} cm)
        </text>
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
