import React, { useState } from "react";
import { AnalysisPanel } from "./AnalysisPanel";
import { Bathroom3DCanvas } from "./Bathroom3DCanvas";
import { BathroomPlanSVG } from "./BathroomPlanSVG";
import { LiveSpacePreview } from "./LiveSpacePreview";
import { VersionDiffPanel } from "./VersionDiffPanel";
import { Icon, type IconName } from "./Icon";
import type {
  DesignState,
  DesignStateDiff,
  PlanMeta,
  RoomLayout,
  VisionEvidence,
} from "../types";

const WALL_ORDER = ["north", "east", "south", "west"] as const;

const WALL_TITLES: Record<string, string> = {
  north: "North",
  east: "East",
  south: "South",
  west: "West",
};

const CATEGORY_GLYPHS: Record<string, IconName> = {
  vanity: "vanity",
  basin: "basin",
  faucet: "basin",
  toilet: "toilet",
  smart_toilet: "toilet",
  shower: "shower",
  smart_shower: "shower",
  bathtub: "bath",
  storage: "archive",
};

export type CanvasModeTab =
  | "2d_plan"
  | "3d_view"
  | "panorama_360"
  | "ar_preview"
  | "elevations"
  | "clearances"
  | "photo"
  | "version_diff";

interface PlanCanvasProps {
  state: DesignState | null;
  layout: RoomLayout | null;
  activeVersion: "v1" | "v2";
  diff: DesignStateDiff | null;
  v1State: DesignState | null;
  meta: PlanMeta | null;
  vision: VisionEvidence | null;
  visionError: string | null;
  uploadedPhotoUrl: string | null;
  onUploadPhoto: (file: File) => void;
  highlightedProductId?: string | null;
  selectedProductId?: string | null;
  onSelectProduct?: (productId: string) => void;
}

export const PlanCanvas: React.FC<PlanCanvasProps> = ({
  state,
  layout,
  activeVersion,
  diff,
  v1State,
  meta,
  vision,
  visionError,
  uploadedPhotoUrl,
  onUploadPhoto,
  highlightedProductId,
  selectedProductId,
  onSelectProduct,
}) => {
  const [canvasTab, setCanvasTab] = useState<CanvasModeTab>("2d_plan");
  const [showVisionDrawer, setShowVisionDrawer] = useState<boolean>(false);
  const [zoomScale, setZoomScale] = useState<number>(1.0);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [panoramaAngle, setPanoramaAngle] = useState<number>(0);

  if (!state || !layout) {
    return (
      <div className="canvas-empty-state">
        <div className="empty-icon">
          <Icon name="plan" size={30} />
        </div>
        <h3>No plan yet</h3>
        <p>Complete the project brief to compute your baseline configuration.</p>
      </div>
    );
  }

  const roomW = state.room_width_ft || 6.0;
  const roomL = state.room_length_ft || 8.0;

  const handleZoomIn = () => setZoomScale((z) => Math.min(1.8, +(z + 0.15).toFixed(2)));
  const handleZoomOut = () => setZoomScale((z) => Math.max(0.65, +(z - 0.15).toFixed(2)));
  const handleResetZoom = () => setZoomScale(1.0);

  return (
    <section className={`studio-column plan-canvas-column ${isFullscreen ? "canvas-fullscreen-mode" : ""}`}>
      {/* Column Header */}
      <div className="column-card-header">
        <div className="header-title-row">
          <span className="column-label">The drawing</span>
          <div className="canvas-status-pills">
            <span className="canvas-meta-pill">
              {activeVersion.toUpperCase()} {activeVersion === "v2" ? "modified" : "baseline"}
            </span>
            <span className="canvas-truth-pill">
              {canvasTab === "2d_plan"
                ? "Solved geometry"
                : canvasTab === "3d_view"
                ? "Solved geometry"
                : canvasTab === "panorama_360"
                ? "Preview only"
                : canvasTab === "ar_preview"
                ? "Preview only"
                : "Measured elevations"}
            </span>
          </div>
        </div>

        <h2 className="column-title">Plan, elevations &amp; room</h2>

        {/* Tab Switcher */}
        <div className="canvas-tabs-nav" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "2d_plan"}
            className={`canvas-tab-btn ${canvasTab === "2d_plan" ? "active" : ""}`}
            onClick={() => setCanvasTab("2d_plan")}
            title="Plan the space · Strict engineering coordinates & clear floors"
          >
            <Icon name="plan" size={13} /> 2D plan
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "3d_view"}
            className={`canvas-tab-btn ${canvasTab === "3d_view" ? "active" : ""}`}
            onClick={() => setCanvasTab("3d_view")}
            title="See the room · Interactive 3D perspective with camera orbit"
          >
            <Icon name="studio" size={13} /> 3D view
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "panorama_360"}
            className={`canvas-tab-btn ${canvasTab === "panorama_360" ? "active" : ""}`}
            onClick={() => setCanvasTab("panorama_360")}
            title="Explore the room · 360-degree architectural panorama preview"
          >
            <Icon name="refresh" size={13} /> 360°
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "ar_preview"}
            className={`canvas-tab-btn ${canvasTab === "ar_preview" ? "active" : ""}`}
            onClick={() => setCanvasTab("ar_preview")}
            title="Preview it in your space · Mobile AR placement guide"
          >
            <Icon name="phone" size={13} /> AR preview
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "elevations"}
            className={`canvas-tab-btn ${canvasTab === "elevations" ? "active" : ""}`}
            onClick={() => setCanvasTab("elevations")}
            title="4-Wall interior elevation schematics"
          >Wall elevations</button>
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "clearances"}
            className={`canvas-tab-btn ${canvasTab === "clearances" ? "active" : ""}`}
            onClick={() => setCanvasTab("clearances")}
            title="Code minimum clearance corridors"
          >
            Clearances
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={canvasTab === "photo"}
            className={`canvas-tab-btn ${canvasTab === "photo" ? "active" : ""}`}
            onClick={() => setCanvasTab("photo")}
            title="Upload bathroom site photo for visual overlay"
          >Photo overlay</button>
          {diff && (
            <button
              type="button"
              role="tab"
              aria-selected={canvasTab === "version_diff"}
              className={`canvas-tab-btn diff-tab-btn ${canvasTab === "version_diff" ? "active" : ""}`}
              onClick={() => setCanvasTab("version_diff")}
              title="Compare Version 1 Baseline with Version 2"
            >
              V1 vs V2 Diff
            </button>
          )}
        </div>
      </div>

      {/* Subtoolbar with interactive controls */}
      <div className="canvas-subtoolbar">
        <div className="canvas-specs">
          <span>
            Boundary: <strong>{roomW.toFixed(1)}′ × {roomL.toFixed(1)}′</strong> (
            {(roomW * 0.3048).toFixed(1)}m × {(roomL * 0.3048).toFixed(1)}m)
          </span>
          {layout.door && (
            <span>
              Door:{" "}
              <strong>
                {layout.door.width_in}″ ({layout.door.wall} wall, {layout.door.swing})
              </strong>
            </span>
          )}
          <span>
            Fixtures: <strong>{layout.placed.length} placed</strong>
          </span>
        </div>

        {/* Toolbar Controls (Zoom, Grid, Fullscreen, Vision toggle) */}
        <div className="canvas-control-actions">
          {canvasTab === "2d_plan" && (
            <div className="zoom-controls-group">
              <button
                type="button"
                className="btn-canvas-ctrl"
                onClick={handleZoomOut}
                title="Zoom out"
                aria-label="Zoom out"
              >
                <Icon name="minus" size={12} title="Zoom out" />
              </button>
              <span className="zoom-scale-text">{Math.round(zoomScale * 100)}%</span>
              <button
                type="button"
                className="btn-canvas-ctrl"
                onClick={handleZoomIn}
                title="Zoom in"
                aria-label="Zoom in"
              >
                <Icon name="plus" size={12} title="Zoom in" />
              </button>
              <button
                type="button"
                className="btn-canvas-ctrl"
                onClick={handleResetZoom}
                title="Reset Zoom to 100%"
              >
                Fit
              </button>
              <button
                type="button"
                className={`btn-canvas-ctrl ${showGrid ? "active-toggle" : ""}`}
                onClick={() => setShowGrid(!showGrid)}
                title="Toggle 12-inch architectural floor grid"
              >
                Grid
              </button>
            </div>
          )}

          <button
            type="button"
            className="btn-canvas-ctrl"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? "Exit fullscreen" : "Expand to fullscreen"}
          >
            {isFullscreen ? (
            <>
              <Icon name="layers" size={12} /> Exit
            </>
          ) : (
            <>
              <Icon name="expand" size={12} /> Fullscreen
            </>
          )}
          </button>

          {meta && (
            <button
              type="button"
              className={`btn-vision-drawer-toggle ${showVisionDrawer ? "active" : ""}`}
              onClick={() => setShowVisionDrawer(!showVisionDrawer)}
              title="Inspect visual observations and unknowns"
            >
              <Icon name="eye" size={12} /> {showVisionDrawer ? "Close evidence" : "Vision & unknowns"}
            </button>
          )}
        </div>
      </div>

      {/* Vision & Advisory Inspection Drawer (Compact) */}
      {showVisionDrawer && meta && (
        <div className="vision-inspection-drawer">
          <AnalysisPanel meta={meta} vision={vision} visionError={visionError} />
        </div>
      )}

      {/* Canvas Viewport Body */}
      <div className="canvas-viewport">
        {/* 1. 2D Architectural Plan View */}
        {canvasTab === "2d_plan" && (
          <div className="canvas-view-content svg-plan-container">
            <BathroomPlanSVG
              layout={layout}
              highlightedProductId={highlightedProductId}
              selectedProductId={selectedProductId}
              onSelectProduct={onSelectProduct}
              showGrid={showGrid}
              zoomScale={zoomScale}
            />
          </div>
        )}

        {/* 2. Interactive 3D Room View */}
        {canvasTab === "3d_view" && (
          <div className="canvas-view-content">
            <Bathroom3DCanvas
              layout={layout}
              selectedProductId={selectedProductId}
              onSelectProduct={onSelectProduct}
            />
          </div>
        )}

        {/* 3. 360° Spherical Room Panorama Preview */}
        {canvasTab === "panorama_360" && (
          <div className="canvas-view-content panorama-view-container">
            <div className="panorama-truth-banner">
              <span className="badge-3d-status">Walk the room · preview only</span>
              <span className="truth-text">
                A schematic walk-around of the four walls, built from the solved layout — not a rendered
                photograph. Drag the slider to turn through the room.
              </span>
            </div>

            <div className="panorama-visual-box">
              <div
                className="panorama-backdrop-sim"
                style={{
                  transform: `translateX(-${(panoramaAngle / 360) * 50}%)`,
                }}
              >
                {WALL_ORDER.map((wall) => {
                  const onThisWall = layout.placed.filter((f) => f.wall === wall);
                  const doorHere = layout.door?.wall === wall;
                  return (
                    <div key={wall} className={`pano-wall wall-${wall}`}>
                      <span className="pano-wall-label">
                        {WALL_TITLES[wall]} Elevation
                        {onThisWall.length > 0
                          ? ` · ${onThisWall.map((f) => f.category.replace(/_/g, " ")).join(" + ")}`
                          : doorHere
                          ? " · Entrance"
                          : " · Clear wall"}
                      </span>
                      {onThisWall.map((f) => (
                        <div key={f.product_id} className="pano-fixture-pin">
                          <Icon name={CATEGORY_GLYPHS[f.category] ?? "box"} size={12} /> {f.product_name}
                        </div>
                      ))}
                      {doorHere && layout.door && (
                        <div className="pano-fixture-pin pin-door">
                          <Icon name="door" size={12} /> Door · {layout.door.width_in}″ {layout.door.swing}
                        </div>
                      )}
                      {onThisWall.length === 0 && !doorHere && (
                        <div className="pano-fixture-pin pin-empty">No fixture on this wall</div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="panorama-crosshair">
                <span className="crosshair-center">+</span>
              </div>
            </div>

            <div className="panorama-controls-bar">
              <span className="control-label">Rotation Angle: {panoramaAngle}°</span>
              <input
                type="range"
                min="0"
                max="360"
                value={panoramaAngle}
                onChange={(e) => setPanoramaAngle(Number(e.target.value))}
                className="panorama-slider"
                aria-label="360 degree rotation slider"
              />
              <div className="quick-angle-buttons">
                <button type="button" onClick={() => setPanoramaAngle(0)}>
                  North (0°)
                </button>
                <button type="button" onClick={() => setPanoramaAngle(90)}>
                  East (90°)
                </button>
                <button type="button" onClick={() => setPanoramaAngle(180)}>
                  South (180°)
                </button>
                <button type="button" onClick={() => setPanoramaAngle(270)}>
                  West (270°)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 4. AR Augmented Reality Space Preview */}
        {canvasTab === "ar_preview" && (
          <div className="canvas-view-content ar-preview-container">
            <div className="ar-truth-banner">
              <span className="badge-3d-status">AR is not available in this build</span>
              <span className="truth-text">
                Room-scale AR is on the roadmap. It is not implemented here, and this screen does not
                place anything in your room.
              </span>
            </div>

            <div className="ar-preview-card">
              <div className="ar-qr-section">
                <div className="ar-instructions">
                  <h4>Why this is not live yet</h4>
                  <p>
                    Placing a fixture at 1:1 scale in your bathroom needs a per-product 3D asset
                    (USDZ for iOS Quick Look, glTF for Android Scene Viewer). The catalog behind this
                    prototype carries dimensions and specifications, not geometry, so there is nothing
                    honest to anchor in your room yet.
                  </p>
                  <h4>What to use instead, today</h4>
                  <ul>
                    <li>
                      <strong>2D plan</strong> — the dimensioned layout every clearance check is
                      actually computed against.
                    </li>
                    <li>
                      <strong>3D room</strong> — the same solved coordinates as a walkable massing
                      model.
                    </li>
                    <li>
                      <strong>Elevations</strong> — wall-by-wall heights and fixture positions.
                    </li>
                  </ul>
                  <p className="ar-disclaimer-note">
                    <strong>Note:</strong> whichever view you work from, a plumber or contractor still has
                    to verify in-wall waste pipes and electrical conduit against the 2D drawing. No
                    visualization can see inside a wall.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 5. 4-Wall Elevation */}
        {canvasTab === "elevations" && (
          <div className="canvas-view-content">
            <LiveSpacePreview
              state={state}
              uploadedImageUrl={uploadedPhotoUrl}
              onUploadImage={onUploadPhoto}
              initialMode="elevations"
            />
          </div>
        )}

        {/* 6. Clearance Envelopes */}
        {canvasTab === "clearances" && (
          <div className="canvas-view-content">
            <LiveSpacePreview
              state={state}
              uploadedImageUrl={uploadedPhotoUrl}
              onUploadImage={onUploadPhoto}
              initialMode="clearance_overlay"
            />
          </div>
        )}

        {/* 7. Photo Overlay Perspective */}
        {canvasTab === "photo" && (
          <div className="canvas-view-content">
            <LiveSpacePreview
              state={state}
              uploadedImageUrl={uploadedPhotoUrl}
              onUploadImage={onUploadPhoto}
              initialMode="photo_perspective"
            />
          </div>
        )}

        {/* 8. Version Diff Panel */}
        {canvasTab === "version_diff" && diff && (
          <div className="canvas-view-content">
            <VersionDiffPanel diff={diff} v1State={v1State} v2State={state} />
          </div>
        )}
      </div>
    </section>
  );
};
