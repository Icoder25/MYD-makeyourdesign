import React, { useState, useEffect } from "react";
import { useEscapeToClose } from "../useEscapeToClose";
import { api, formatMoney } from "../api";
import type {
  ClientExportData,
  DealerExportData,
  DesignerExportData,
  ExportPackageResponse,
} from "../types";

interface ExportModalProps {
  projectId: string;
  versionId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  projectId,
  versionId,
  isOpen,
  onClose,
}) => {
  useEscapeToClose(isOpen, onClose);

  const [role, setRole] = useState<"client" | "designer" | "dealer">("client");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportData, setExportData] = useState<any>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    api
      .getExportPackage(projectId, role, versionId)
      .then((res: ExportPackageResponse) => {
        setExportData(res.data);
      })
      .catch((err) => setError(err.message || "Failed to fetch export package"))
      .finally(() => setLoading(false));
  }, [isOpen, role, projectId, versionId]);

  if (!isOpen) return null;

  const handlePrintableOpen = () => {
    const url = api.getExportDocumentUrl(projectId, role, versionId);
    window.open(url, "_blank");
  };

  const handleCopyBOM = () => {
    if (role === "dealer" && exportData && exportData.line_items) {
      const items = (exportData as DealerExportData).line_items;
      const tsv = [
        "Item\tCategory\tFamily\tSKU\tProduct\tQty\tUnit Price\tRough-in\tElectrical",
        ...items.map(
          (i) =>
            `${i.item_number}\t${i.category}\t${i.kohler_family}\t${i.sku}\t${i.product_name}\t${i.quantity}\t${i.unit_price}\t${i.rough_in_in ?? "N/A"}\t${i.electrical_required ? "Yes" : "No"}`,
        ),
      ].join("\n");
      navigator.clipboard.writeText(tsv);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const clientData = role === "client" ? (exportData as ClientExportData) : null;
  const designerData = role === "designer" ? (exportData as DesignerExportData) : null;
  const dealerData = role === "dealer" ? (exportData as DealerExportData) : null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card" role="dialog" aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "920px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <span className="badge-luxury">AUDITABLE ARCHITECTURAL EXPORT</span>
            <h2 style={{ margin: "6px 0 0", fontSize: "20px", fontWeight: 700, color: "var(--ink-900)" }}>
              Project Specification & BOM Packages
            </h2>
          </div>
          <button className="btn-icon-close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        {/* Role Tab Navigation */}
        <div
          style={{
            display: "flex",
            gap: "8px",
            borderBottom: "1px solid var(--border-light)",
            paddingBottom: "12px",
            marginTop: "14px",
          }}
        >
          <button
            type="button"
            className={role === "client" ? "btn-chip active" : "btn-chip"}
            onClick={() => setRole("client")}
          >
            Client Presentation
          </button>
          <button
            type="button"
            className={role === "designer" ? "btn-chip active" : "btn-chip"}
            onClick={() => setRole("designer")}
          >
            Designer Architectural Spec
          </button>
          <button
            type="button"
            className={role === "dealer" ? "btn-chip active" : "btn-chip"}
            onClick={() => setRole("dealer")}
          >
            Dealer / Contractor BOM
          </button>
        </div>

        {error && <div className="callout callout-danger" style={{ margin: "16px 0" }}>{error}</div>}

        {loading ? (
          <div style={{ padding: "40px 0", textAlign: "center", color: "var(--ink-500)" }}>
            Compiling verified architectural package...
          </div>
        ) : (
          <div style={{ maxHeight: "62vh", overflowY: "auto", padding: "16px 0" }}>
            {/* TAB 1: CLIENT PRESENTATION */}
            {role === "client" && clientData && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div
                  style={{
                    background: "var(--sand-50)",
                    padding: "16px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-light)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <span style={{ fontSize: "11px", color: "var(--ink-500)", textTransform: "uppercase" }}>
                      ESTIMATED INVESTMENT
                    </span>
                    <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--ink-900)" }}>
                      {formatMoney(clientData.total_investment, clientData.currency)}
                    </div>
                  </div>
                  {clientData.water_litres_saved_annually && (
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: "11px", color: "var(--ink-500)", textTransform: "uppercase" }}>
                        WATER CONSERVATION
                      </span>
                      <div style={{ fontSize: "20px", fontWeight: 700, color: "#15803d" }}>
                        {clientData.water_litres_saved_annually.toLocaleString()} L / yr
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ fontSize: "12px", color: "var(--ink-600)" }}>
                  Project: {clientData.project_id} · Room: {clientData.room_dimensions} · Version: {clientData.version_id.toUpperCase()}
                </div>

                <table className="table" style={{ width: "100%", fontSize: "13px" }}>
                  <thead>
                    <tr>
                      <th>Fixture</th>
                      <th>Category</th>
                      <th>Tier</th>
                      <th style={{ textAlign: "right" }}>List Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clientData.products.map((p, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong>{p.name}</strong>
                          <div style={{ fontSize: "11px", color: "var(--ink-500)" }}>{p.dimensions}</div>
                        </td>
                        <td style={{ textTransform: "capitalize" }}>{p.category}</td>
                        <td style={{ textTransform: "capitalize" }}>{p.tier}</td>
                        <td style={{ textAlign: "right", fontWeight: 600 }}>
                          {formatMoney(p.price, p.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* TAB 2: DESIGNER ARCHITECTURAL SPEC */}
            {role === "designer" && designerData && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                  <h4 style={{ margin: "0 0 8px", fontSize: "13px", color: "var(--ink-800)" }}>
                    Verified Clearances & Wall Anchors
                  </h4>
                  <table className="table" style={{ width: "100%", fontSize: "12px" }}>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Wall</th>
                        <th>Footprint</th>
                        <th>Required Clearance</th>
                        <th>Standard</th>
                      </tr>
                    </thead>
                    <tbody>
                      {designerData.clearances.map((c, idx) => (
                        <tr key={idx}>
                          <td><strong>{c.product_name}</strong> ({c.category})</td>
                          <td style={{ textTransform: "capitalize" }}>{c.wall}</td>
                          <td>{c.footprint}</td>
                          <td>{c.required_clearance}</td>
                          <td style={{ fontSize: "11px", color: "var(--ink-500)" }}>{c.clearance_source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div>
                  <h4 style={{ margin: "12px 0 8px", fontSize: "13px", color: "var(--ink-800)" }}>
                    Audit Decision Memory Log
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {designerData.decision_records.length === 0 ? (
                      <div style={{ fontSize: "12px", color: "var(--ink-500)", fontStyle: "italic" }}>
                        Initial baseline configuration (V1). No prior trade-off decisions recorded.
                      </div>
                    ) : (
                      designerData.decision_records.map((d, idx) => (
                        <div
                          key={idx}
                          style={{
                            background: "var(--sand-50)",
                            padding: "10px 12px",
                            borderRadius: "4px",
                            border: "1px solid var(--border-light)",
                            fontSize: "12px",
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "var(--primary-deep)", textTransform: "capitalize" }}>
                            {d.category} · {d.action.replace("_", " ")}
                          </div>
                          <div style={{ color: "var(--ink-700)", marginTop: "2px" }}>
                            {d.rationale}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: DEALER / CONTRACTOR BOM */}
            {role === "dealer" && dealerData && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: "12px", color: "var(--ink-600)" }}>
                    {dealerData.line_items.length} catalog line items · Total Net:{" "}
                    <strong>{formatMoney(dealerData.total_net_price, dealerData.currency)}</strong>
                  </div>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleCopyBOM}
                    style={{ fontSize: "11px", padding: "4px 10px" }}
                  >
                    {copied ? "✓ Copied Tab-Delimited!" : "Copy Schedule to Clipboard"}
                  </button>
                </div>

                <table className="table" style={{ width: "100%", fontSize: "12px" }}>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Family</th>
                      <th>SKU Code</th>
                      <th>Description</th>
                      <th>Qty</th>
                      <th>Rough-In</th>
                      <th>Electrical</th>
                      <th style={{ textAlign: "right" }}>Unit Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dealerData.line_items.map((item) => (
                      <tr key={item.item_number}>
                        <td>{item.item_number}</td>
                        <td style={{ fontWeight: 600, color: "var(--primary-deep)" }}>{item.kohler_family}</td>
                        <td>
                          <code style={{ fontSize: "11px", background: "#f1f5f9", padding: "2px 4px", borderRadius: "3px" }}>
                            {item.sku}
                          </code>
                        </td>
                        <td>{item.product_name}</td>
                        <td>{item.quantity}</td>
                        <td>{item.rough_in_in ? `${item.rough_in_in}"` : "—"}</td>
                        <td>{item.electrical_required ? "⚡ Required" : "No"}</td>
                        <td style={{ textAlign: "right", fontWeight: 600 }}>
                          {formatMoney(item.unit_price, item.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        <div
          className="modal-footer"
          style={{
            marginTop: "16px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: "1px solid var(--border-light)",
            paddingTop: "12px",
          }}
        >
          <div style={{ fontSize: "11px", color: "var(--ink-500)" }}>
            Every product code, dimension and price in this package is read straight from the catalog and
            the solved layout — no language model writes into it. Prices are illustrative prototype
            figures, not KOHLER quotations.
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button className="btn-secondary" onClick={onClose}>
              Close
            </button>
            <button className="btn-primary" onClick={handlePrintableOpen}>
              Open Standalone Printable Spec ↗
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
