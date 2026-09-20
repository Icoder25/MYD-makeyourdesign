import React, { useState } from "react";
import { formatMoney } from "../api";
import type { DesignState, PlanResponse } from "../types";
import { useEscapeToClose } from "../useEscapeToClose";
import { Icon } from "./Icon";

export interface SavedProjectRecord {
  id: string;
  name: string;
  timestamp: string;
  dimensions: string;
  totalPrice: number;
  currency: string;
  productsCount: number;
  plan: PlanResponse;
  activeDesignState: DesignState;
  v1DesignState?: DesignState | null;
}

interface MyDesignsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  savedProjects: SavedProjectRecord[];
  currentProjectId: string | null;
  onLoadProject: (record: SavedProjectRecord) => void;
  onSaveCurrentProject: (name: string) => void;
  onDeleteProject: (id: string) => void;
  hasActivePlan: boolean;
}

export const MyDesignsDrawer: React.FC<MyDesignsDrawerProps> = ({
  isOpen,
  onClose,
  savedProjects,
  currentProjectId,
  onLoadProject,
  onSaveCurrentProject,
  onDeleteProject,
  hasActivePlan,
}) => {
  useEscapeToClose(isOpen, onClose);

  const [newProjectName, setNewProjectName] = useState<string>("");
  const [isSaving, setIsSaving] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    onSaveCurrentProject(newProjectName.trim());
    setNewProjectName("");
    setIsSaving(false);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card my-designs-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Saved designs"
        style={{ maxWidth: "680px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">Saved work</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>Saved projects</h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            <Icon name="close" size={13} />
          </button>
        </div>

        <p style={{ margin: "10px 0 16px", fontSize: "13px", color: "var(--ink-600)" }}>
          Switch between saved layouts, reload previous versions, or save current active planning states. All projects
          persist locally in your browser storage.
        </p>

        {/* Save Current State Bar */}
        {hasActivePlan && (
          <div className="save-current-panel">
            {!isSaving ? (
              <div className="save-current-prompt">
                <span>Save your current workspace state to local projects:</span>
                <button
                  type="button"
                  className="primary"
                  onClick={() => setIsSaving(true)}
                  style={{ fontSize: "0.84rem", padding: "0.4rem 0.9rem" }}
                >Save this project</button>
              </div>
            ) : (
              <form className="save-current-form" onSubmit={handleSave}>
                <input
                  type="text"
                  className="save-input"
                  placeholder="e.g. Modern Serenity Master Bath"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  autoFocus
                  required
                />
                <button type="submit" className="primary" style={{ fontSize: "0.84rem" }}>
                  Save
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setIsSaving(false)}
                  style={{ fontSize: "0.84rem" }}
                >
                  Cancel
                </button>
              </form>
            )}
          </div>
        )}

        {/* Saved Projects List */}
        <div className="saved-projects-list">
          {savedProjects.length === 0 ? (
            <div className="empty-projects-state">
              <p>No saved projects found. Create or generate a plan to save it here.</p>
            </div>
          ) : (
            savedProjects.map((p) => {
              const isCurrent = currentProjectId === p.id;
              const dateStr = new Date(p.timestamp).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
                year: "numeric",
              });

              return (
                <div
                  key={p.id}
                  className={`saved-project-card ${isCurrent ? "is-active-project" : ""}`}
                >
                  <div className="project-card-main">
                    <div className="project-card-meta">
                      <h4 className="project-card-name">{p.name}</h4>
                      {isCurrent && <span className="active-badge">Currently active</span>}
                    </div>
                    <div className="project-specs-line">
                      <span>{p.dimensions}</span>
                      <span className="dot-sep">•</span>
                      <span>{p.productsCount} Line Items</span>
                      <span className="dot-sep">•</span>
                      <span>{formatMoney(p.totalPrice, p.currency)}</span>
                      <span className="dot-sep">•</span>
                      <span className="date-tag">{dateStr}</span>
                    </div>
                  </div>

                  <div className="project-card-actions">
                    <button
                      type="button"
                      className="btn-load-project"
                      onClick={() => {
                        onLoadProject(p);
                        onClose();
                      }}
                      disabled={isCurrent}
                      title={isCurrent ? "Currently active in workspace" : "Load this project"}
                    >
                      {isCurrent ? "Loaded" : "Open"}
                    </button>
                    <button
                      type="button"
                      className="btn-delete-project"
                      onClick={() => onDeleteProject(p.id)}
                      title="Remove from saved projects"
                    >
                      <Icon name="trash" size={14} title="Delete project" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
