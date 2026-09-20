import React from "react";
import { formatMoney } from "../api";
import type { DoorSpec } from "../types";
import { Icon } from "./Icon";

export type WorkflowStep = "brief" | "design" | "refine" | "finalize";
export type AppTheme = "light" | "dark" | "system";

interface WorkspaceHeaderProps {
  projectId: string;
  projectName?: string;
  /** Null until a plan exists. The header must not invent a room. */
  roomWidthFt: number | null;
  roomLengthFt: number | null;
  budget: number | null;
  currency?: string;
  styles: string[];
  door?: DoorSpec | null;
  hasPlan: boolean;
  activeVersion: "v1" | "v2";
  hasV2: boolean;
  onSelectVersion: (ver: "v1" | "v2") => void;
  isFinalized: boolean;
  requiresVerification: boolean;
  catalogSize: number;
  llmAvailable: boolean;
  visionAvailable: boolean;
  currentStep?: WorkflowStep;
  theme: AppTheme;
  onSelectTheme: (theme: AppTheme) => void;
  saveStatusText?: string;
  onSaveProject?: () => void;
  onOpenInspiration: () => void;
  onOpenBrief: () => void;
  onOpenFinalize: () => void;
  onOpenExport: () => void;
  onOpenHelp?: () => void;
  onCompareVersions?: () => void;
}

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({
  projectId,
  projectName = "Modern Serenity",
  roomWidthFt,
  roomLengthFt,
  budget,
  currency = "INR",
  styles,
  door,
  hasPlan,
  activeVersion,
  hasV2,
  onSelectVersion,
  isFinalized,
  requiresVerification,
  catalogSize,
  llmAvailable,
  visionAvailable,
  currentStep = "design",
  theme,
  onSelectTheme,
  saveStatusText = "Saved just now",
  onSaveProject,
  onOpenInspiration,
  onOpenBrief,
  onOpenFinalize,
  onOpenExport,
  onOpenHelp,
  onCompareVersions,
}) => {
  const getReadinessBadge = () => {
    if (!hasPlan) {
      return <span className="status-badge-studio status-pending">No design yet</span>;
    }
    if (isFinalized) {
      return <span className="status-badge-studio status-finalized">
          <Icon name="lock" size={11} /> Finalized &amp; locked
        </span>;
    }
    if (requiresVerification) {
      return (
        <span className="status-badge-studio status-pending">
          <Icon name="warn" size={11} /> Pending verification
        </span>
      );
    }
    return <span className="status-badge-studio status-ready">Design ready</span>;
  };

  const formattedStyles =
    styles.length > 0
      ? styles.map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(" · ")
      : "No style preference set";

  const roomDimensionsDisplay =
    roomWidthFt != null && roomLengthFt != null
      ? `${(roomWidthFt * 0.3048).toFixed(1)}m × ${(roomLengthFt * 0.3048).toFixed(1)}m · ` +
        `${(roomWidthFt * 0.3048 * roomLengthFt * 0.3048).toFixed(2)} m² ` +
        `(${roomWidthFt.toFixed(1)}′ × ${roomLengthFt.toFixed(1)}′)`
      : "Room not measured yet";

  // The door description has to follow the door the plan was actually solved
  // against; a fixed "Left / Inward Swing" is wrong the moment anyone picks a
  // sliding door, and the swing is a clearance input, not decoration.
  const doorDisplay = door
    ? `${door.wall.charAt(0).toUpperCase()}${door.wall.slice(1)} wall · ${door.width_in}″ · ${door.swing}`
    : "Door not specified";

  return (
    <header className="workspace-header-combined" role="banner">
      {/* Top Bar: Workflow Stepper & Global Controls */}
      <div className="header-workflow-bar">
        {/* Workflow Stepper */}
        <div className="workflow-stepper" role="navigation" aria-label="Planning workflow">
          <button
            type="button"
            className={`step-item ${
              currentStep === "brief" ? "current" : hasPlan ? "completed" : "next"
            }`}
            onClick={onOpenBrief}
            title="Edit room boundary, doors, and requirements"
          >
            <span className="step-num">1</span>
            <div className="step-meta">
              <span className="step-title">Brief</span>
              <span className="step-desc">Space &amp; Needs</span>
            </div>
          </button>
          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-item ${
              currentStep === "design" ? "current" : hasPlan ? "completed" : "next"
            }`}
            onClick={() => onSelectVersion("v1")}
            title="Baseline 2D spatial layout and fixture clearances"
          >
            <span className="step-num">2</span>
            <div className="step-meta">
              <span className="step-title">Design</span>
              <span className="step-desc">Feasible plan</span>
            </div>
          </button>
          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-item ${currentStep === "refine" || hasV2 ? "current" : "next"}`}
            onClick={() => {
              if (hasV2) onSelectVersion("v2");
            }}
            title="Evaluate modifications and trade-offs in DesignPulse"
          >
            <span className="step-num">3</span>
            <div className="step-meta">
              <span className="step-title">Refine</span>
              <span className="step-desc">DesignPulse™</span>
            </div>
          </button>
          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-item ${isFinalized ? "completed" : "next"}`}
            onClick={onOpenFinalize}
            title="Sign off on verification checklist and lock design"
          >
            <span className="step-num">4</span>
            <div className="step-meta">
              <span className="step-title">Finalize</span>
              <span className="step-desc">Audit &amp; BOM</span>
            </div>
          </button>
        </div>

        {/* Global Toolbar: Save Status, Help, Theme Controls, Save Project */}
        <div className="header-quick-controls">
          <span className="save-status-indicator">{saveStatusText}</span>

          {onSaveProject && (
            <button
              type="button"
              className="btn-header-save"
              onClick={onSaveProject}
              title="Save current project to local storage"
            >Save project</button>
          )}

          {/* Theme Selector (Light / Dark / System) */}
          <div className="theme-toggle-cluster" role="radiogroup" aria-label="Appearance">
            <button
              type="button"
              className={`btn-theme-pill ${theme === "light" ? "active" : ""}`}
              onClick={() => onSelectTheme("light")}
              title="Light theme (Warm White & Stone)"
              aria-checked={theme === "light"}
              role="radio"
            >
              <Icon name="sun" size={12} /> Light
            </button>
            <button
              type="button"
              className={`btn-theme-pill ${theme === "dark" ? "active" : ""}`}
              onClick={() => onSelectTheme("dark")}
              title="Dark theme (Charcoal & Graphite)"
              aria-checked={theme === "dark"}
              role="radio"
            >
              <Icon name="moon" size={12} /> Dark
            </button>
            <button
              type="button"
              className={`btn-theme-pill ${theme === "system" ? "active" : ""}`}
              onClick={() => onSelectTheme("system")}
              title="System preference"
              aria-checked={theme === "system"}
              role="radio"
            >
              <Icon name="monitor" size={12} /> Auto
            </button>
          </div>

          {onOpenHelp && (
            <button
              type="button"
              className="btn-header-help"
              onClick={onOpenHelp}
              title="How this works"
              aria-label="Help and documentation"
            >
              ? Help
            </button>
          )}
        </div>
      </div>

      {/* Bottom Row: Compact Project Context Strip */}
      <div className="header-context-strip">
        <div className="project-context-info">
          <div className="project-name-cluster">
            <h1 className="project-title">{projectName}</h1>
            <span className="project-code">({projectId.length > 10 ? projectId.slice(0, 8) : projectId})</span>
            {getReadinessBadge()}
          </div>

          <div className="project-attributes-row">
            <span className="attr-dim">{roomDimensionsDisplay}</span>
            <span className="dot-sep">•</span>
            <span className="attr-budget">
              {budget !== null ? `Budget: ${formatMoney(budget, currency)}` : "No budget cap"}
            </span>
            <span className="dot-sep">•</span>
            <span className="attr-style">{formattedStyles}</span>
            <span className="dot-sep">•</span>
            <span className="attr-door">{doorDisplay}</span>
            <span className="dot-sep">•</span>
            <span
              className="catalog-meta"
              title="Prototype catalog. Products are modelled on KOHLER product classes; prices are illustrative."
            >
              {catalogSize > 0 ? `${catalogSize} catalog products · illustrative` : "Catalog unavailable"}
            </span>
            <span className="dot-sep">•</span>
            <span className={`service-flag${llmAvailable ? " is-on" : ""}`}>
              AI {llmAvailable ? "on" : "off"}
            </span>
            <span className="dot-sep">•</span>
            <span className={`service-flag${visionAvailable ? " is-on" : ""}`}>
              Vision {visionAvailable ? "on" : "off"}
            </span>
          </div>
        </div>

        {/* Version Switcher & Primary Action Buttons */}
        <div className="header-context-actions">
          <button
            type="button"
            className="btn-context-action"
            onClick={onOpenInspiration}
            title="Curate architectural styles and materials"
          >
            <Icon name="spark" size={14} /> Inspiration
          </button>

          <div className="version-pill-group">
            <button
              type="button"
              className={`version-pill-btn ${activeVersion === "v1" ? "active" : ""}`}
              onClick={() => onSelectVersion("v1")}
            >V1 baseline</button>
            <button
              type="button"
              className={`version-pill-btn ${activeVersion === "v2" ? "active" : ""}`}
              onClick={() => onSelectVersion("v2")}
              disabled={!hasV2}
              title={!hasV2 ? "Create a change in DesignPulse to unlock V2" : "View Version 2"}
            >
              {hasV2 ? "V2 active" : "V2 (unmodified)"}
            </button>
          </div>

          {hasV2 && onCompareVersions && (
            <button
              type="button"
              className="btn-context-action"
              onClick={onCompareVersions}
              title="Compare Version 1 Baseline with Version 2"
            >
              Compare
            </button>
          )}

          <button
            type="button"
            className="btn-context-action btn-context-primary"
            onClick={onOpenExport}
            title="Export packages & dealer BOM"
          >
            Export BOM
          </button>
        </div>
      </div>
    </header>
  );
};
