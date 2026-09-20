import React from "react";
import { useEscapeToClose } from "../useEscapeToClose";
import { BriefForm } from "./BriefForm";
import type { PlanRequest } from "../api";

interface BriefDrawerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (req: PlanRequest) => void;
  onImageSelected: (file: File) => void;
  busy: boolean;
  visionAvailable: boolean;
  imageName: string | null;
}

export const BriefDrawerModal: React.FC<BriefDrawerModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  onImageSelected,
  busy,
  visionAvailable,
  imageName,
}) => {
  useEscapeToClose(isOpen, onClose);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card brief-drawer-card" role="dialog" aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "560px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">PROJECT SETUP &amp; PARAMETERS</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              Bathroom Dimensions &amp; Brief
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <p style={{ margin: "10px 0 16px", fontSize: "13px", color: "var(--ink-600)" }}>
          Modify room dimensions, budget ceiling, or door placement. Modifying the brief re-runs the deterministic planner.
        </p>

        <div className="brief-drawer-body">
          <BriefForm
            onSubmit={(req) => {
              onSubmit(req);
              onClose();
            }}
            onImageSelected={onImageSelected}
            busy={busy}
            visionAvailable={visionAvailable}
            imageName={imageName}
          />
        </div>
      </div>
    </div>
  );
};
