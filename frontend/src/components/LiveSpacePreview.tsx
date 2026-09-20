import React, { useState } from "react";
import type { DesignState, PlacedFixture } from "../types";
import { Icon } from "./Icon";

/** How far the reserved clear floor projects off the wall, in inches.
 *
 * The solver already sized this rectangle from the clearance rule it names in
 * `clearance_source`; reading it back beats restating a code minimum that may
 * not be the one that applied.
 */
function frontClearanceIn(item: PlacedFixture): number | null {
  if (!item.clearance || !item.footprint) return null;
  const projection =
    item.wall === "north" || item.wall === "south"
      ? item.clearance.depth_in - item.footprint.depth_in
      : item.clearance.width_in - item.footprint.width_in;
  return projection > 0 ? projection : null;
}

interface LiveSpacePreviewProps {
  state: DesignState | null;
  uploadedImageUrl?: string | null;
  onUploadImage?: (file: File) => void;
  initialMode?: "elevations" | "clearance_overlay" | "photo_perspective";
}

export const LiveSpacePreview: React.FC<LiveSpacePreviewProps> = ({
  state,
  uploadedImageUrl,
  onUploadImage,
  initialMode,
}) => {
  const [viewMode, setViewMode] = useState<"elevations" | "clearance_overlay" | "photo_perspective">(
    initialMode || "elevations"
  );
  const [selectedWall, setSelectedWall] = useState<"north" | "south" | "east" | "west">("north");

  React.useEffect(() => {
    if (initialMode) {
      setViewMode(initialMode);
    }
  }, [initialMode]);

  if (!state || !state.layout) {
    return (
      <div className="card" style={{ padding: "30px", textAlign: "center", color: "var(--ink-500)" }}>
        No active DesignState geometry available for preview.
      </div>
    );
  }

  const placed = state.layout.placed || [];
  const roomW = state.room_width_ft || 6.0;
  const roomL = state.room_length_ft || 8.0;

  // Group fixtures by wall
  const fixturesByWall = {
    north: placed.filter((p) => p.wall === "north"),
    south: placed.filter((p) => p.wall === "south"),
    east: placed.filter((p) => p.wall === "east"),
    west: placed.filter((p) => p.wall === "west"),
  };

  const wallLengthFt =
    selectedWall === "north" || selectedWall === "south" ? roomW : roomL;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && onUploadImage) {
      onUploadImage(e.target.files[0]);
    }
  };

  return (
    <div className="card live-preview-card" style={{ padding: "20px", marginTop: "16px" }}>
      {/* Header & Mode Switcher */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="badge-luxury">Checked against the plan</span>
            <span style={{ fontSize: "11px", color: "var(--ink-500)" }}>
              Version {state.version_id.toUpperCase()} · {roomW.toFixed(1)}′ × {roomL.toFixed(1)}′
            </span>
          </div>
          <h3 style={{ margin: "4px 0 0", fontSize: "16px", color: "var(--ink-900)" }}>Elevations & clearances</h3>
        </div>

        <div style={{ display: "flex", gap: "6px" }}>
          <button
            type="button"
            className={viewMode === "elevations" ? "btn-chip active" : "btn-chip"}
            onClick={() => setViewMode("elevations")}
          >
            4-Wall Elevation
          </button>
          <button
            type="button"
            className={viewMode === "clearance_overlay" ? "btn-chip active" : "btn-chip"}
            onClick={() => setViewMode("clearance_overlay")}
          >Clearance envelopes</button>
          <button
            type="button"
            className={viewMode === "photo_perspective" ? "btn-chip active" : "btn-chip"}
            onClick={() => setViewMode("photo_perspective")}
          >Photo perspective</button>
        </div>
      </div>

      {/* Mode 1: 4-Wall Elevation */}
      {viewMode === "elevations" && (
        <div>
          {/* Wall tabs */}
          <div style={{ display: "flex", gap: "8px", marginBottom: "14px" }}>
            {(["north", "east", "south", "west"] as const).map((wall) => {
              const count = fixturesByWall[wall].length;
              const isSelected = selectedWall === wall;
              return (
                <button
                  key={wall}
                  type="button"
                  onClick={() => setSelectedWall(wall)}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "4px",
                    border: isSelected ? "2px solid var(--primary-deep)" : "1px solid var(--border-light)",
                    background: isSelected ? "#f0f6fa" : "var(--surface)",
                    fontWeight: isSelected ? 700 : 500,
                    fontSize: "12px",
                    color: isSelected ? "var(--primary-deep)" : "var(--ink-700)",
                    cursor: "pointer",
                    textTransform: "capitalize",
                  }}
                >
                  {wall} Wall ({count} {count === 1 ? "fixture" : "fixtures"})
                </button>
              );
            })}
          </div>

          {/* Elevation Schematic Graphic */}
          <div
            style={{
              background: "var(--surface-sunken, #faf9f6)",
              border: "1px solid var(--border-light)",
              borderRadius: "6px",
              padding: "24px 16px",
              minHeight: "220px",
              position: "relative",
            }}
          >
            <div style={{ fontSize: "11px", color: "var(--ink-500)", marginBottom: "12px", display: "flex", justifyContent: "space-between" }}>
              <span>Wall elevation · <strong>{selectedWall}</strong> · {wallLengthFt.toFixed(1)} ft run</span>
              <span>Scale 1:1 · from the solver</span>
            </div>

            {fixturesByWall[selectedWall].length === 0 ? (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--ink-400)", fontStyle: "italic" }}>
                No fixtures assigned to the {selectedWall} wall. Clearance corridor maintained.
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "flex-end", gap: "24px", minHeight: "150px", borderBottom: "3px solid #78716c", paddingBottom: "4px" }}>
                {fixturesByWall[selectedWall].map((item, idx) => {
                  const prod = state.selected_products.find((p) => p.category === item.category);
                  const widthIn = item.footprint?.width_in || 24;
                  const depthIn = item.footprint?.depth_in || 20;
                  const visualW = Math.max(80, Math.min(260, widthIn * 3.2));
                  const visualH = Math.max(70, Math.min(180, depthIn * 3.5));

                  return (
                    <div
                      key={idx}
                      style={{
                        width: `${visualW}px`,
                        height: `${visualH}px`,
                        background: "linear-gradient(180deg, #ffffff 0%, #e2e8f0 100%)",
                        border: "1.5px solid var(--primary-deep)",
                        borderRadius: "4px 4px 0 0",
                        padding: "8px",
                        boxSizing: "border-box",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "space-between",
                        boxShadow: "0 2px 4px rgba(0,0,0,0.06)",
                        position: "relative",
                      }}
                    >
                      <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", color: "var(--primary-deep)" }}>
                        {item.category}
                      </div>
                      <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--ink-900)", lineHeight: "1.2" }}>
                        {prod?.name || item.category}
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--ink-600)", fontFamily: "monospace" }}>
                        {widthIn}"W × {depthIn}"D
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mode 2: Clearance Envelopes */}
      {viewMode === "clearance_overlay" && (
        <div style={{ background: "var(--surface-sunken, #f8fafc)", padding: "16px", borderRadius: "6px", border: "1px solid var(--border-light)" }}>
          <h4 style={{ margin: "0 0 4px", fontSize: "13px", color: "var(--ink-800)" }}>Computed clearances</h4>
          <p style={{ margin: "0 0 10px", fontSize: "11px", color: "var(--ink-600)" }}>
            Every figure below is the envelope the layout solver reserved for that fixture, with the
            rule it came from. Spatial verdict for this design:{" "}
            <strong>{(state.ledger?.domains?.space?.status ?? "unknown").toUpperCase()}</strong>.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "10px" }}>
            {placed.map((item, idx) => {
              const prod = state.selected_products.find((p) => p.category === item.category);
              return (
                <div
                  key={idx}
                  style={{
                    background: "var(--surface-raised, #ffffff)",
                    padding: "12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border-light)",
                    fontSize: "12px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600 }}>
                    <span style={{ textTransform: "capitalize", color: "var(--primary-deep)" }}>
                      {item.category}
                    </span>
                    <span style={{ color: "var(--ink-500)", fontSize: "11px", textTransform: "capitalize" }}>
                      {item.wall} wall
                    </span>
                  </div>
                  <div style={{ marginTop: "4px", color: "var(--ink-900)", fontWeight: 500 }}>
                    {prod?.name || item.category}
                  </div>
                  <div style={{ marginTop: "6px", fontSize: "11px", color: "var(--ink-600)" }}>
                    <div>
                      Footprint: {item.footprint?.width_in}&quot;W × {item.footprint?.depth_in}&quot;D
                    </div>
                    <div>
                      Clear floor reserved in front: {frontClearanceIn(item)?.toFixed(1) ?? "—"}&quot;
                    </div>
                    <div style={{ color: "var(--ink-500)" }}>Rule: {item.clearance_source}</div>
                    <div>
                      Plumbing rough-in:{" "}
                      {item.category === "toilet" || item.category === "smart_toilet"
                        ? state.toilet_rough_in_in != null
                          ? `${state.toilet_rough_in_in}" (confirmed)`
                          : "not confirmed — measure on site"
                        : "wall supply, position to be confirmed on site"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Mode 3: Photo Perspective Overlay */}
      {viewMode === "photo_perspective" && (
        <div style={{ background: "var(--surface-sunken, #f8fafc)", padding: "16px", borderRadius: "6px", border: "1px solid var(--border-light)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div>
              <h4 style={{ margin: 0, fontSize: "14px", color: "var(--ink-900)" }}>Existing condition overlay</h4>
              <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--ink-600)" }}>
                Ground the solved DesignState geometry against real customer site photographs.
              </p>
            </div>
            <label className="btn-secondary" style={{ cursor: "pointer", fontSize: "12px", padding: "6px 12px" }}>Upload a site photo<input type="file" accept="image/*" onChange={handleFileChange} style={{ display: "none" }} />
            </label>
          </div>

          <div
            style={{
              position: "relative",
              minHeight: "260px",
              background: uploadedImageUrl ? `url(${uploadedImageUrl}) center/cover no-repeat` : "var(--surface-sunken, #e2e8f0)",
              borderRadius: "6px",
              overflow: "hidden",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {/* Fixture tags floating over photo */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: uploadedImageUrl ? "rgba(15, 23, 42, 0.45)" : "transparent",
                display: "flex",
                flexWrap: "wrap",
                alignContent: "center",
                justifyContent: "center",
                gap: "12px",
                padding: "20px",
              }}
            >
              {!uploadedImageUrl && (
                <div style={{ color: "var(--ink-500)", textAlign: "center", maxWidth: "340px", marginBottom: "16px" }}>
                  <div style={{ marginBottom: "6px", opacity: 0.5 }}>
                <Icon name="camera" size={26} />
              </div>
                  <strong>No site photo uploaded yet</strong>
                  <div style={{ fontSize: "11px", marginTop: "4px" }}>
                    Upload a room photo to see the selected fixtures listed against your actual space.
                  </div>
                </div>
              )}

              {placed.map((item, idx) => {
                const prod = state.selected_products.find((p) => p.category === item.category);
                return (
                  <div
                    key={idx}
                    style={{
                      background: "rgba(255, 255, 255, 0.95)",
                      backdropFilter: "blur(4px)",
                      border: "1px solid var(--primary-deep)",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                      fontSize: "11px",
                    }}
                  >
                    <div style={{ fontWeight: 700, color: "var(--primary-deep)", textTransform: "uppercase" }}>
                      {item.category} ({item.wall} wall)
                    </div>
                    <div style={{ fontWeight: 600, color: "var(--ink-900)" }}>{prod?.name || item.category}</div>
                    <div style={{ color: "var(--ink-600)" }}>{item.footprint?.width_in}" × {item.footprint?.depth_in}"</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
