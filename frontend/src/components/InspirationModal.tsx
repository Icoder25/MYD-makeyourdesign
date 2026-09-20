import React, { useState, useEffect } from "react";
import { api } from "../api";
import type { InspirationStylePreset, InspirationApplyResponse } from "../types";
import { useEscapeToClose } from "../useEscapeToClose";

interface InspirationModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onPresetApplied: (res: InspirationApplyResponse) => void;
}

export const InspirationModal: React.FC<InspirationModalProps> = ({
  projectId,
  isOpen,
  onClose,
  onPresetApplied,
}) => {
  useEscapeToClose(isOpen, onClose);

  const [presets, setPresets] = useState<InspirationStylePreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>("warm_minimalist");
  const [customQuery, setCustomQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [applying, setApplying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    api
      .getInspirationPresets()
      .then((res) => {
        setPresets(res.presets);
        if (res.presets.length > 0 && !selectedPresetId) {
          setSelectedPresetId(res.presets[0].id);
        }
      })
      .catch((err) => setError(err.message || "Failed to load inspiration presets"))
      .finally(() => setLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  const selectedPreset = presets.find((p) => p.id === selectedPresetId) || presets[0];

  const handleApply = async (presetIdToApply?: string) => {
    setApplying(true);
    setError(null);
    try {
      const pid = presetIdToApply ?? selectedPresetId;
      const res = await api.applyInspiration(projectId, {
        preset_id: pid || undefined,
        query: customQuery.trim() ? customQuery.trim() : undefined,
      });
      onPresetApplied(res);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to apply inspiration direction.");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card inspiration-modal-card" role="dialog" aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "860px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">ARCHITECTURAL DESIGN INSPIRATION</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              KOHLER Collection Directions
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <p style={{ margin: "12px 0 16px", color: "var(--ink-600)", fontSize: "13px", lineHeight: "1.5" }}>
          Curate materials, hardware finishes, and fixture families.
          <strong style={{ color: "var(--primary-deep)" }}> Feeds DesignState through the brief:</strong> clearances,
          plumbing rough-ins, and budget limits are strictly preserved.
        </p>

        {error && <div className="callout callout-danger" style={{ marginBottom: "16px" }}>{error}</div>}

        {loading ? (
          <div style={{ padding: "40px 0", textAlign: "center", color: "var(--ink-500)" }}>
            Loading KOHLER architectural presets...
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: "20px", maxHeight: "60vh", overflowY: "auto" }}>
            {/* Preset Selector Sidebar */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {presets.map((preset) => {
                const isSelected = preset.id === (selectedPreset?.id);
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => {
                      setSelectedPresetId(preset.id);
                      setCustomQuery("");
                    }}
                    style={{
                      textAlign: "left",
                      padding: "12px 14px",
                      borderRadius: "6px",
                      border: isSelected ? "2px solid var(--primary-deep)" : "1px solid var(--border-light)",
                      background: isSelected ? "#f4f8fb" : "var(--surface)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ fontWeight: isSelected ? 700 : 600, fontSize: "14px", color: "var(--ink-900)" }}>
                      {preset.title}
                    </div>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "var(--ink-500)",
                        marginTop: "4px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {preset.tagline}
                    </div>
                    {/* Palette swatches */}
                    <div style={{ display: "flex", gap: "4px", marginTop: "8px" }}>
                      {preset.palette_tones.map((hex, idx) => (
                        <span
                          key={idx}
                          style={{
                            width: "16px",
                            height: "16px",
                            borderRadius: "3px",
                            backgroundColor: hex,
                            border: "1px solid rgba(0,0,0,0.15)",
                            display: "inline-block",
                          }}
                        />
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Preset Details & Customizer */}
            {selectedPreset && (
              <div
                style={{
                  background: "var(--sand-50)",
                  border: "1px solid var(--border-light)",
                  borderRadius: "8px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <h3 style={{ margin: 0, fontSize: "18px", color: "var(--ink-900)" }}>
                      {selectedPreset.title}
                    </h3>
                    <span style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--primary-deep)", fontWeight: 600 }}>
                      KOHLER Curated
                    </span>
                  </div>
                  <p style={{ margin: "6px 0 0", fontSize: "13px", fontStyle: "italic", color: "var(--ink-700)" }}>
                    "{selectedPreset.tagline}"
                  </p>
                  <p style={{ margin: "10px 0 0", fontSize: "12px", lineHeight: "1.6", color: "var(--ink-600)" }}>
                    {selectedPreset.description}
                  </p>
                </div>

                {/* Aesthetic Dimensions Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "12px" }}>
                  <div style={{ background: "white", padding: "10px 12px", borderRadius: "6px", border: "1px solid var(--border-light)" }}>
                    <span style={{ fontWeight: 600, color: "var(--ink-700)", display: "block", marginBottom: "4px" }}>
                      PRIMARY MATERIALS
                    </span>
                    <span style={{ color: "var(--ink-900)" }}>
                      {selectedPreset.primary_materials.join(" · ")}
                    </span>
                  </div>
                  <div style={{ background: "white", padding: "10px 12px", borderRadius: "6px", border: "1px solid var(--border-light)" }}>
                    <span style={{ fontWeight: 600, color: "var(--ink-700)", display: "block", marginBottom: "4px" }}>
                      HARDWARE FINISHES
                    </span>
                    <span style={{ color: "var(--ink-900)" }}>
                      {selectedPreset.hardware_finishes.join(" · ")}
                    </span>
                  </div>
                  <div style={{ background: "white", padding: "10px 12px", borderRadius: "6px", border: "1px solid var(--border-light)" }}>
                    <span style={{ fontWeight: 600, color: "var(--ink-700)", display: "block", marginBottom: "4px" }}>
                      RECOMMENDED FAMILIES
                    </span>
                    <span style={{ color: "var(--primary-deep)", fontWeight: 600 }}>
                      {selectedPreset.recommended_families.join(", ")}
                    </span>
                  </div>
                  <div style={{ background: "white", padding: "10px 12px", borderRadius: "6px", border: "1px solid var(--border-light)" }}>
                    <span style={{ fontWeight: 600, color: "var(--ink-700)", display: "block", marginBottom: "4px" }}>
                      COLOR PALETTE
                    </span>
                    <div style={{ display: "flex", gap: "6px", alignItems: "center", marginTop: "2px" }}>
                      {selectedPreset.palette_tones.map((hex, idx) => (
                        <span
                          key={idx}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            fontSize: "10px",
                            fontFamily: "monospace",
                            color: "var(--ink-600)",
                          }}
                        >
                          <span
                            style={{
                              width: "14px",
                              height: "14px",
                              borderRadius: "2px",
                              backgroundColor: hex,
                              border: "1px solid rgba(0,0,0,0.15)",
                            }}
                          />
                          {hex}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Optional Custom Style Prompt */}
                <div style={{ marginTop: "4px" }}>
                  <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--ink-700)", display: "block", marginBottom: "4px" }}>
                    OPTIONAL: NATURAL LANGUAGE ADJUSTMENT
                  </label>
                  <input
                    type="text"
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    placeholder="e.g. Add fluted glass shower enclosure and brushed brass accents"
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--border-light)",
                      fontSize: "12px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div className="modal-footer" style={{ marginTop: "20px", display: "flex", justifyContent: "flex-end", gap: "12px" }}>
          <button className="btn-secondary" onClick={onClose} disabled={applying}>
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={() => handleApply()}
            disabled={applying || loading || !selectedPreset}
            style={{ minWidth: "180px" }}
          >
            {applying ? "Recomputing Design..." : `Apply ${selectedPreset?.title || "Preset"}`}
          </button>
        </div>
      </div>
    </div>
  );
};
