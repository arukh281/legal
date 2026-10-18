import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  uploadCaseImportFile,
  previewCaseImport,
  commitCaseImport,
  getImportTemplateUrl,
  getCaseImportReportUrl,
  type CaseImportUploadResponse,
  type CaseImportCommitResponse,
} from "../api/client";

interface ImportCasesPageProps {
  onBack: () => void;
}

export const ImportCasesPage: React.FC<ImportCasesPageProps> = ({ onBack }) => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<CaseImportUploadResponse | null>(null);
  const [commitResult, setCommitResult] = useState<CaseImportCommitResponse | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [mapping, setMapping] = useState<Record<string, number>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const STANDARD_FIELDS: Array<{ key: string; label: string; required?: boolean }> = [
    { key: "client_name", label: "Client Name", required: true },
    { key: "client_type", label: "Client Type (Individual, Company, LLP, etc.)" },
    { key: "cin_or_pan", label: "CIN or PAN" },
    { key: "matter_title", label: "Matter Title", required: true },
    { key: "case_type", label: "Case Type (e.g. Insolvency, Commercial Suit)" },
    { key: "court_or_forum", label: "Court or Forum (e.g. NCLT New Delhi Bench II)" },
    { key: "case_number", label: "Case Number" },
    { key: "next_hearing_date", label: "Next Hearing Date (Day-first DD/MM/YYYY or YYYY-MM-DD)" },
    { key: "lead_lawyer_email", label: "Lead Lawyer Email" },
    { key: "notes", label: "Notes / Summary" },
  ];

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadCaseImportFile(file),
    onSuccess: (data) => {
      setUploadResult(data);
      setMapping(data.mapping || {});
      if (data.sheet_names && data.sheet_names.length > 0) {
        setSelectedSheet(data.sheet_names[0]);
      }
      setErrorMsg(null);
      setStep(2);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Failed to upload file. Please check file format and size limit.");
    },
  });

  const previewMutation = useMutation({
    mutationFn: () => {
      if (!uploadResult) throw new Error("No import in progress.");
      return previewCaseImport(uploadResult.import_id, {
        mapping,
        sheet_name: selectedSheet || undefined,
      });
    },
    onSuccess: (data) => {
      setUploadResult(data);
      setErrorMsg(null);
      setStep(3);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Failed to update preview.");
    },
  });

  const commitMutation = useMutation({
    mutationFn: () => {
      if (!uploadResult) throw new Error("No import in progress.");
      return commitCaseImport(uploadResult.import_id);
    },
    onSuccess: (data) => {
      setCommitResult(data);
      setErrorMsg(null);
      setStep(4);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Failed to commit import. Verify file rows and advisory lock.");
    },
  });

  const summary = (uploadResult?.preview as any)?.summary || {};
  const previewRows = (uploadResult?.preview as any)?.rows || [];

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "16px 20px 48px 20px" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <button
          onClick={onBack}
          style={{
            background: "none",
            border: "none",
            color: "var(--accent)",
            fontSize: "14px",
            fontWeight: "600",
            cursor: "pointer",
            padding: 0,
            marginBottom: "8px",
          }}
        >
          ← Back to Matters
        </button>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1 style={{ fontSize: "24px", fontWeight: "700", margin: 0 }}>Import Live Cases</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
              Batch import your firm's existing matters, clients, and hearing dates from Excel or CSV.
            </p>
          </div>

          {/* Stepper indicator */}
          <div style={{ display: "flex", gap: "8px", alignItems: "center", fontSize: "12px", fontWeight: "600" }}>
            <span style={{ color: step >= 1 ? "var(--accent)" : "var(--text-muted)" }}>1. Upload</span>
            <span>→</span>
            <span style={{ color: step >= 2 ? "var(--accent)" : "var(--text-muted)" }}>2. Map Columns</span>
            <span>→</span>
            <span style={{ color: step >= 3 ? "var(--accent)" : "var(--text-muted)" }}>3. Preview</span>
            <span>→</span>
            <span style={{ color: step >= 4 ? "var(--success)" : "var(--text-muted)" }}>4. Complete</span>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div
          style={{
            backgroundColor: "rgba(239, 68, 68, 0.15)",
            border: "1px solid var(--danger)",
            borderRadius: "8px",
            padding: "12px 16px",
            color: "var(--danger)",
            fontSize: "13px",
            marginBottom: "20px",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Step 1: Upload */}
      {step === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Download template banner */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "14px",
            }}
          >
            <div>
              <div style={{ fontSize: "15px", fontWeight: "700" }}>Need a sample template?</div>
              <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>
                Download standard formatted spreadsheets with pre-configured column headers.
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <a
                href={getImportTemplateUrl("xlsx")}
                download="cases_import_template.xlsx"
                style={{
                  padding: "8px 14px",
                  borderRadius: "6px",
                  backgroundColor: "var(--bg-primary)",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  fontSize: "12px",
                  fontWeight: "600",
                  textDecoration: "none",
                }}
              >
                📊 Excel Template (.xlsx)
              </a>
              <a
                href={getImportTemplateUrl("csv")}
                download="cases_import_template.csv"
                style={{
                  padding: "8px 14px",
                  borderRadius: "6px",
                  backgroundColor: "var(--bg-primary)",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  fontSize: "12px",
                  fontWeight: "600",
                  textDecoration: "none",
                }}
              >
                📄 CSV Template (.csv)
              </a>
            </div>
          </div>

          {/* Upload card */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "2px dashed var(--border)",
              borderRadius: "12px",
              padding: "48px 24px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>📁</div>
            <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "6px" }}>
              Select an Excel or CSV file
            </h3>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", maxWidth: "480px", margin: "0 auto 20px auto" }}>
              Supports .xlsx and .csv files up to 10 MB and 5,000 rows. Files containing macros (.xlsm) or VBA code are rejected for security.
            </p>

            <input
              type="file"
              id="case-import-file-input"
              accept=".xlsx,.csv"
              style={{ display: "none" }}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
            />

            <div style={{ display: "flex", justifyContent: "center", gap: "12px", alignItems: "center" }}>
              <label
                htmlFor="case-import-file-input"
                style={{
                  padding: "10px 20px",
                  borderRadius: "6px",
                  backgroundColor: "var(--bg-primary)",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Browse File...
              </label>

              {selectedFile && (
                <button
                  onClick={() => uploadMutation.mutate(selectedFile)}
                  disabled={uploadMutation.isPending}
                  style={{
                    padding: "10px 24px",
                    borderRadius: "6px",
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    border: "none",
                    fontSize: "13px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {uploadMutation.isPending ? "Parsing File..." : `Upload ${selectedFile.name}`}
                </button>
              )}
            </div>

            {selectedFile && (
              <div style={{ marginTop: "12px", fontSize: "13px", color: "var(--text-muted)" }}>
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 2: Column Mapping */}
      {step === 2 && uploadResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {uploadResult.warning && (
            <div
              style={{
                backgroundColor: "rgba(245, 158, 11, 0.12)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                borderRadius: "8px",
                padding: "12px 16px",
                color: "#f59e0b",
                fontSize: "13px",
              }}
            >
              ⚠️ {uploadResult.warning}
            </div>
          )}

          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "20px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
              <div>
                <h3 style={{ fontSize: "16px", fontWeight: "700", margin: 0 }}>Map Columns</h3>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Confirm how the columns in your file match the required case fields.
                </p>
              </div>

              {uploadResult.sheet_names && uploadResult.sheet_names.length > 1 && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <label style={{ fontSize: "12px", fontWeight: "600" }}>Sheet:</label>
                  <select
                    value={selectedSheet}
                    onChange={(e) => setSelectedSheet(e.target.value)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: "6px",
                      border: "1px solid var(--border)",
                      backgroundColor: "var(--bg-primary)",
                      color: "var(--text-primary)",
                      fontSize: "13px",
                    }}
                  >
                    {uploadResult.sheet_names.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {STANDARD_FIELDS.map((f) => (
                <div
                  key={f.key}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px 0",
                    borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                  }}
                >
                  <div style={{ flex: 1, minWidth: "200px" }}>
                    <span style={{ fontSize: "13px", fontWeight: "600" }}>
                      {f.label} {f.required && <span style={{ color: "var(--danger)" }}>*</span>}
                    </span>
                  </div>

                  <div style={{ width: "260px" }}>
                    <select
                      value={mapping[f.key] !== undefined ? mapping[f.key] : -1}
                      onChange={(e) => {
                        const val = parseInt(e.target.value, 10);
                        setMapping((prev) => {
                          const next = { ...prev };
                          if (val === -1) {
                            delete next[f.key];
                          } else {
                            next[f.key] = val;
                          }
                          return next;
                        });
                      }}
                      style={{
                        width: "100%",
                        padding: "6px 10px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        backgroundColor: "var(--bg-primary)",
                        color: "var(--text-primary)",
                        fontSize: "13px",
                      }}
                    >
                      <option value={-1}>-- Not mapped --</option>
                      {uploadResult.headers.map((h, idx) => (
                        <option key={idx} value={idx}>
                          Column {idx + 1}: {h || `(Header ${idx + 1})`}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "24px" }}>
              <button
                onClick={() => setStep(1)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  background: "none",
                  cursor: "pointer",
                }}
              >
                ← Change File
              </button>

              <button
                onClick={() => previewMutation.mutate()}
                disabled={previewMutation.isPending}
                style={{
                  padding: "8px 24px",
                  borderRadius: "6px",
                  backgroundColor: "var(--accent)",
                  color: "#fff",
                  border: "none",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                {previewMutation.isPending ? "Generating Preview..." : "Review Preview →"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Preview */}
      {step === 3 && uploadResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Summary Metric Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "12px" }}>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>Total Rows</div>
              <div style={{ fontSize: "22px", fontWeight: "700", marginTop: "4px" }}>{summary.total_rows || 0}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>New Clients</div>
              <div style={{ fontSize: "22px", fontWeight: "700", color: "var(--accent)", marginTop: "4px" }}>{summary.new_clients || 0}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>Matched Clients</div>
              <div style={{ fontSize: "22px", fontWeight: "700", color: "var(--success)", marginTop: "4px" }}>{summary.existing_clients_matched || 0}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>New Matters</div>
              <div style={{ fontSize: "22px", fontWeight: "700", color: "var(--accent)", marginTop: "4px" }}>{summary.new_matters || 0}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>Hearings</div>
              <div style={{ fontSize: "22px", fontWeight: "700", marginTop: "4px" }}>{summary.total_hearings || 0}</div>
            </div>
          </div>

          {/* Table of Rows */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "20px",
            }}
          >
            <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "14px" }}>Preview Cases</h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left", color: "var(--text-muted)" }}>
                    <th style={{ padding: "8px" }}>Row</th>
                    <th style={{ padding: "8px" }}>Client</th>
                    <th style={{ padding: "8px" }}>Matter Title</th>
                    <th style={{ padding: "8px" }}>Case No</th>
                    <th style={{ padding: "8px" }}>Hearing Date</th>
                    <th style={{ padding: "8px" }}>Status</th>
                    <th style={{ padding: "8px" }}>Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {previewRows.map((r: any) => (
                    <tr
                      key={r.row_number}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                        backgroundColor: r.status === "DUPLICATE_SKIPPED" ? "rgba(245, 158, 11, 0.06)" : "transparent",
                      }}
                    >
                      <td style={{ padding: "10px 8px" }}>{r.row_number}</td>
                      <td style={{ padding: "10px 8px" }}>
                        <div style={{ fontWeight: "600" }}>{r.client_name}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{r.client_match_action}</div>
                      </td>
                      <td style={{ padding: "10px 8px" }}>{r.matter_title}</td>
                      <td style={{ padding: "10px 8px" }}>{r.case_number_normalized || r.case_number_raw || "—"}</td>
                      <td style={{ padding: "10px 8px" }}>{r.next_hearing_date || "—"}</td>
                      <td style={{ padding: "10px 8px" }}>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "4px",
                            fontSize: "11px",
                            fontWeight: "600",
                            backgroundColor:
                              r.status === "NEW_MATTER"
                                ? "rgba(16, 185, 129, 0.15)"
                                : "rgba(245, 158, 11, 0.15)",
                            color:
                              r.status === "NEW_MATTER" ? "var(--success)" : "#f59e0b",
                          }}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td style={{ padding: "10px 8px", color: "var(--text-muted)", fontSize: "12px" }}>
                        {r.warnings && r.warnings.length > 0 ? r.warnings.join("; ") : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "24px" }}>
              <button
                onClick={() => setStep(2)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  background: "none",
                  cursor: "pointer",
                }}
              >
                ← Back to Mapping
              </button>

              <button
                onClick={() => {
                  if (window.confirm("Commit these cases into your firm workspace? This will atomically create clients, matters, and listings under an advisory lock.")) {
                    commitMutation.mutate();
                  }
                }}
                disabled={commitMutation.isPending}
                style={{
                  padding: "10px 28px",
                  borderRadius: "6px",
                  backgroundColor: "var(--success)",
                  color: "#fff",
                  border: "none",
                  fontWeight: "700",
                  fontSize: "14px",
                  cursor: "pointer",
                }}
              >
                {commitMutation.isPending ? "Committing Import..." : "Commit Cases to Firm"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Completion */}
      {step === 4 && commitResult && uploadResult && (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            padding: "36px 24px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "42px", marginBottom: "12px" }}>🎉</div>
          <h2 style={{ fontSize: "22px", fontWeight: "700", marginBottom: "8px" }}>
            Case Import Completed Successfully!
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "28px" }}>
            All records were committed atomically to the firm ledger with full audit provenance.
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              gap: "12px",
              maxWidth: "680px",
              margin: "0 auto 32px auto",
            }}
          >
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>CLIENTS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String((commitResult.counts as any)?.clients_created ?? 0)}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>MATTERS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String((commitResult.counts as any)?.matters_created ?? 0)}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>HEARINGS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String((commitResult.counts as any)?.hearings_created ?? 0)}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>CASE LINKS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String((commitResult.counts as any)?.case_links_created ?? 0)}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: "14px" }}>
            <a
              href={getCaseImportReportUrl(uploadResult.import_id)}
              download={`import_report_${uploadResult.import_id}.csv`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 20px",
                borderRadius: "6px",
                backgroundColor: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                fontSize: "13px",
                fontWeight: "600",
                textDecoration: "none",
              }}
            >
              📥 Download Sanitized Audit Report (.csv)
            </a>

            <button
              onClick={onBack}
              style={{
                padding: "10px 24px",
                borderRadius: "6px",
                backgroundColor: "var(--accent)",
                color: "#fff",
                border: "none",
                fontSize: "13px",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              View Matters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
