import React, { useState } from "react";
import { formatMoney } from "../api";
import type { ConstraintLedger, DesignState } from "../types";
import { useEscapeToClose } from "../useEscapeToClose";

interface FinalizeModalProps {
  isOpen: boolean;
  onClose: () => void;
  state: DesignState | null;
  ledger: ConstraintLedger | null;
  isFinalized: boolean;
  onFinalizeConfirm: () => void;
  onOpenExport: () => void;
}

export const FinalizeModal: React.FC<FinalizeModalProps> = ({
  isOpen,
  onClose,
  state,
  ledger,
  isFinalized,
  onFinalizeConfirm,
  onOpenExport,
}) => {
  useEscapeToClose(isOpen, onClose);

  const [confirmedDimensions, setConfirmedDimensions] = useState<boolean>(isFinalized);
  const [confirmedPlumbing, setConfirmedPlumbing] = useState<boolean>(isFinalized);
  const [confirmedClientApproval, setConfirmedClientApproval] = useState<boolean>(isFinalized);

  if (!isOpen || !state) return null;

  const verificationChecks = ledger?.domains.verification.checks || [];
  const allConfirmed = confirmedDimensions && confirmedPlumbing && confirmedClientApproval;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card finalize-modal-card" role="dialog" aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "680px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">AUDITABLE ARCHITECTURAL SIGN-OFF</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              {isFinalized ? "Specification Finalized & Locked" : "Finalize Architectural Specification"}
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <p style={{ margin: "12px 0 16px", color: "var(--ink-600)", fontSize: "13px", lineHeight: "1.5" }}>
          Finalization seals Version <strong>{state.version_id.toUpperCase()}</strong>. It confirms that field dimensions,
          drain locations, and electrical availability have been reviewed before generating purchase orders and dealer BOMs.
        </p>

        {/* Specification Snapshot */}
        <div className="finalize-spec-snapshot">
          <div className="snapshot-cell">
            <span className="cell-title">VERSION</span>
            <span className="cell-body font-mono">{state.version_id.toUpperCase()}</span>
          </div>
          <div className="snapshot-cell">
            <span className="cell-title">DIMENSIONS</span>
            <span className="cell-body">
              {state.room_width_ft}′ × {state.room_length_ft}′
            </span>
          </div>
          <div className="snapshot-cell">
            <span className="cell-title">TOTAL INVESTMENT</span>
            <span className="cell-body font-mono">
              {formatMoney(state.total_price, state.currency)}
            </span>
          </div>
          <div className="snapshot-cell">
            <span className="cell-title">FIXTURES</span>
            <span className="cell-body">{state.selected_products.length} line items</span>
          </div>
        </div>

        {/* Verification Requirements Checklist */}
        <div className="finalize-checklist-section">
          <h4 style={{ margin: "16px 0 8px", fontSize: "13px", color: "var(--ink-800)" }}>
            FIELD VERIFICATION REQUIREMENTS (7 DOMAINS)
          </h4>

          {verificationChecks.length > 0 ? (
            <ul className="finalize-verification-list">
              {verificationChecks.map((chk, idx) => (
                <li key={idx} className="verify-list-item">
                  <span className="verify-icon">⚠</span>
                  <div className="verify-text">
                    <strong>{chk.constraint.replace(/_/g, " ")}</strong>: {chk.reason}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="callout callout-success" style={{ margin: "8px 0 14px", fontSize: "12px" }}>
              ✓ All standard clearances and rough-in tolerances satisfied.
            </div>
          )}
        </div>

        {/* Sign-Off Confirmation Checkboxes */}
        <div className="finalize-signoff-boxes">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={confirmedDimensions}
              disabled={isFinalized}
              onChange={(e) => setConfirmedDimensions(e.target.checked)}
            />
            <span>
              I have physically verified finished room dimensions and door swing clearances.
            </span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={confirmedPlumbing}
              disabled={isFinalized}
              onChange={(e) => setConfirmedPlumbing(e.target.checked)}
            />
            <span>
              Toilet rough-in ({state.toilet_rough_in_in || 12}&quot;) and plumbing supply lines are verified.
            </span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={confirmedClientApproval}
              disabled={isFinalized}
              onChange={(e) => setConfirmedClientApproval(e.target.checked)}
            />
            <span>
              Client has reviewed design rationale and approved selected KOHLER fixture package.
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="finalize-modal-footer">
          {!isFinalized ? (
            <button
              type="button"
              className="btn-finalize-primary"
              disabled={!allConfirmed}
              onClick={() => {
                onFinalizeConfirm();
              }}
            >
              🔒 Lock &amp; Finalize Specification
            </button>
          ) : (
            <div className="finalized-actions-row">
              <span className="finalized-lock-indicator">
                ✓ Specification Locked for Construction
              </span>
              <button
                type="button"
                className="btn-studio-action btn-studio-primary"
                onClick={() => {
                  onClose();
                  onOpenExport();
                }}
              >
                📄 Proceed to Dealer BOM Export →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
