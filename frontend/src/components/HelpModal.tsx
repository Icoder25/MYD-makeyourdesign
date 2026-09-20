import React from "react";
import { useEscapeToClose } from "../useEscapeToClose";
import { Icon } from "./Icon";

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  useEscapeToClose(isOpen, onClose);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card help-modal-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="KOHLER AI BathPlan User Guide"
        style={{ maxWidth: "720px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">SYSTEM ARCHITECTURE &amp; GUIDANCE</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              How KOHLER AI BathPlan Works
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            <Icon name="close" size={13} />
          </button>
        </div>

        <div className="help-content-scrollable">
          <section className="help-section">
            <h3 className="help-heading">
          <Icon name="plan" size={15} /> The four-step professional workflow
        </h3>
            <div className="workflow-help-grid">
              <div className="workflow-step-card">
                <strong>1. Brief</strong>
                <p>Define room dimensions, entrance doors, plumbing rough-in status, and aesthetic style directions.</p>
              </div>
              <div className="workflow-step-card">
                <strong>2. Design</strong>
                <p>The deterministic solver checks all NKBA/IRC clearances and computes a compliant 2D baseline layout.</p>
              </div>
              <div className="workflow-step-card">
                <strong>3. Refine</strong>
                <p>Use DesignPulse™ to test changes (e.g. wider vanity) and inspect spatial & financial ripple effects.</p>
              </div>
              <div className="workflow-step-card">
                <strong>4. Finalize</strong>
                <p>Review the 7-domain ledger, sign off on field verification items, and generate dealer BOM packages.</p>
              </div>
            </div>
          </section>

          <section className="help-section">
            <h3 className="help-heading">
          <Icon name="pulse" size={15} /> DesignPulse™ consequence engine
        </h3>
            <p className="help-text">
              Traditional CAD tools require you to manually reposition every fixture when changing a layout. DesignPulse
              calculates the exact ripple effect of any alteration:
            </p>
            <ul className="help-list">
              <li>
                <strong>Affected vs Unchanged:</strong> Clearly distinguishes modified fixtures from unchanged elements.
              </li>
              <li>
                <strong>Feasibility Guarantees:</strong> Never approves impossible placements or violations of code clearances.
              </li>
              <li>
                <strong>Explainable Trade-offs:</strong> If a change reduces clearance, it tells you why and offers viable alternatives.
              </li>
            </ul>
          </section>

          <section className="help-section">
            <h3 className="help-heading">
          <Icon name="studio" size={15} /> Spatial intent vs visualisation aids
        </h3>
            <p className="help-text">
              <strong>The 2D plan</strong> represents strict engineering geometry and code-required clear floor spaces.
              <strong> 3D, 360°, and AR</strong> are visualization aids to help you imagine materials and finishes. We never
              substitute visual rendering for engineering verification.
            </p>
          </section>

          <section className="help-section">
            <h3 className="help-heading">
          <Icon name="keyboard" size={15} /> Keyboard &amp; accessibility shortcuts
        </h3>
            <div className="shortcuts-grid">
              <div className="shortcut-row">
                <kbd>Esc</kbd>
                <span>Close any open modal or drawer</span>
              </div>
              <div className="shortcut-row">
                <kbd>Tab</kbd>
                <span>Navigate through interactive fixtures &amp; controls</span>
              </div>
              <div className="shortcut-row">
                <kbd>Mouse drag</kbd>
                <span>Orbit 3D camera angle</span>
              </div>
              <div className="shortcut-row">
                <kbd>Scroll wheel</kbd>
                <span>Zoom the plan and the 3D room</span>
              </div>
            </div>
          </section>
        </div>

        <div className="modal-footer" style={{ marginTop: "14px" }}>
          <button type="button" className="primary" onClick={onClose}>Got it</button>
        </div>
      </div>
    </div>
  );
};
