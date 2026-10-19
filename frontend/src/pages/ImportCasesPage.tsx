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

interface CaseNumberInfo {
  raw: string;
  normalized?: string;
  parseable?: boolean;
}

interface ImportPreviewRow {
  row_number: number;
  client_name: string;
  client_type?: string;
  client_role?: string;
  client_status?: string;
  matched_client_id?: string | null;
  cin?: string | null;
  pan?: string | null;
  matter_title: string;
  matter_status: string;
  matched_matter_id?: string | null;
  match_reason?: string | null;
  case_type?: string | null;
  court_or_forum?: string | null;
  case_numbers?: CaseNumberInfo[];
  hearing_date?: string | null;
  lead_lawyer_email?: string | null;
  lead_user_id?: string | null;
  suggested_client_id?: string | null;
  suggested_client_name?: string | null;
  notes?: string | null;
  warnings?: string[];
}

interface ImportSummary {
  total_rows?: number;
  new_clients?: number;
  existing_clients?: number;
  new_matters?: number;
  existing_matters?: number;
  hearings_to_create?: number;
  warnings_count?: number;
}

interface CommitCounts {
  clients_created?: number;
  matters_created?: number;
  hearings_created?: number;
  case_links_created?: number;
  skipped_existing_matters?: number;
}

interface RowOverride {
  action: string;
  client_id?: string;
}

export const ImportCasesPage: React.FC<ImportCasesPageProps> = ({ onBack }) => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<CaseImportUploadResponse | null>(null);
  const [commitResult, setCommitResult] = useState<CaseImportCommitResponse | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [mapping, setMapping] = useState<Record<string, number>>({});
  const [clientOverrides, setClientOverrides] = useState<Record<string, RowOverride>>({});
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
      setClientOverrides({});
      if (data.sheet_names && data.sheet_names.length > 0) {
        setSelectedSheet(data.sheet_names[0]);
      }
      setErrorMsg(null);
      setStep(2);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Failed to upload file.";
      setErrorMsg(msg);
    },
  });

  const previewMutation = useMutation({
    mutationFn: (overridesToUse?: Record<string, RowOverride>) => {
      if (!uploadResult) throw new Error("No import in progress.");
      const currentOverrides = overridesToUse !== undefined ? overridesToUse : clientOverrides;
      return previewCaseImport(uploadResult.import_id, {
        mapping,
        client_overrides: currentOverrides,
        sheet_name: selectedSheet || undefined,
      });
    },
    onSuccess: (data) => {
      setUploadResult(data);
      setErrorMsg(null);
      setStep(3);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Failed to update preview.";
      setErrorMsg(msg);
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
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Failed to commit import. Verify file rows and advisory lock.";
      setErrorMsg(msg);
    },
  });

  const handleApplyOverride = (rowNum: number, override: RowOverride) => {
    const nextOverrides = {
      ...clientOverrides,
      [String(rowNum)]: override,
    };
    setClientOverrides(nextOverrides);
    previewMutation.mutate(nextOverrides);
  };

  const handleRemoveOverride = (rowNum: number) => {
    const nextOverrides = { ...clientOverrides };
    delete nextOverrides[String(rowNum)];
    setClientOverrides(nextOverrides);
    previewMutation.mutate(nextOverrides);
  };

  const summary: ImportSummary = (uploadResult?.preview as { summary?: ImportSummary } | undefined)?.summary || {};
  const previewRows: ImportPreviewRow[] = (uploadResult?.preview as { rows?: ImportPreviewRow[] } | undefined)?.rows || [];
  const commitCounts: CommitCounts = (commitResult?.counts as CommitCounts | undefined) || {};

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
              padding: "16px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div>
              <div style={{ fontWeight: "600", fontSize: "14px" }}>Need a spreadsheet template?</div>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                Download our pre-formatted template with guidance and expected column headers.
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <a
                href={getImportTemplateUrl("xlsx")}
                download="cases_import_template.xlsx"
                style={{
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  fontSize: "12px",
                  textDecoration: "none",
                  backgroundColor: "var(--bg-primary)",
                }}
              >
                📥 Excel Template (.xlsx)
              </a>
              <a
                href={getImportTemplateUrl("csv")}
                download="cases_import_template.csv"
                style={{
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  fontSize: "12px",
                  textDecoration: "none",
                  backgroundColor: "var(--bg-primary)",
                }}
              >
                📥 CSV Template
              </a>
            </div>
          </div>

          {/* Upload Dropzone */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "2px dashed var(--border)",
              borderRadius: "12px",
              padding: "40px 20px",
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "12px",
            }}
          >
            <div style={{ fontSize: "40px" }}>📄</div>
            <div style={{ fontSize: "16px", fontWeight: "600" }}>
              Choose an Excel (.xlsx, .xls) or CSV file to import
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", maxWidth: "420px" }}>
              Files up to 10MB and 5,000 rows are supported. Formula injection protection, duplicate checking, and Indian date parsing are applied automatically.
            </div>

            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              id="file-upload-input"
              style={{ display: "none" }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
            />

            <label
              htmlFor="file-upload-input"
              style={{
                marginTop: "12px",
                padding: "8px 20px",
                borderRadius: "6px",
                backgroundColor: "var(--accent)",
                color: "#fff",
                fontWeight: "600",
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              Select File from Computer
            </label>

            {selectedFile && (
              <div style={{ marginTop: "12px", fontSize: "13px", color: "var(--text-primary)", fontWeight: "500" }}>
                Selected: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>

          {selectedFile && (
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                onClick={() => uploadMutation.mutate(selectedFile)}
                disabled={uploadMutation.isPending}
                style={{
                  padding: "10px 24px",
                  borderRadius: "6px",
                  backgroundColor: "var(--accent)",
                  color: "#fff",
                  border: "none",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                {uploadMutation.isPending ? "Uploading and Inspecting..." : "Upload & Continue →"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Column Mapping */}
      {step === 2 && uploadResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {uploadResult.warning && (
            <div
              style={{
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                border: "1px solid #f59e0b",
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h3 style={{ fontSize: "16px", fontWeight: "700", margin: 0 }}>Map Columns</h3>
                <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Confirm which columns in your spreadsheet match the expected firm fields.
                </p>
              </div>

              {uploadResult.sheet_names && uploadResult.sheet_names.length > 1 && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <label style={{ fontSize: "12px", color: "var(--text-muted)" }}>Sheet:</label>
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
              <div style={{ fontSize: "22px", fontWeight: "700", color: "var(--success)", marginTop: "4px" }}>{summary.existing_clients || 0}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>New Matters</div>
              <div style={{ fontSize: "22px", fontWeight: "700", color: "var(--accent)", marginTop: "4px" }}>{summary.new_matters || 0}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>Hearings</div>
              <div style={{ fontSize: "22px", fontWeight: "700", marginTop: "4px" }}>{summary.hearings_to_create || 0}</div>
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "700", margin: 0 }}>Preview Cases</h3>
              {previewMutation.isPending && (
                <span style={{ fontSize: "12px", color: "var(--accent)" }}>Updating preview...</span>
              )}
            </div>
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
                    <th style={{ padding: "8px" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {previewRows.map((r) => {
                    const currentOverride = clientOverrides[String(r.row_number)];
                    const isFlagged =
                      r.matter_status === "ALREADY_EXISTS" ||
                      Boolean(
                        r.warnings &&
                          r.warnings.some(
                            (w) =>
                              w.toLowerCase().includes("duplicate") ||
                              w.toLowerCase().includes("already exists"),
                          ),
                      );

                    return (
                      <tr
                        key={r.row_number}
                        style={{
                          borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                          backgroundColor:
                            r.matter_status === "ALREADY_EXISTS" ? "rgba(245, 158, 11, 0.06)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "10px 8px" }}>{r.row_number}</td>
                        <td style={{ padding: "10px 8px" }}>
                          <div style={{ fontWeight: "600" }}>{r.client_name}</div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{r.client_status}</div>
                        </td>
                        <td style={{ padding: "10px 8px" }}>{r.matter_title}</td>
                        <td style={{ padding: "10px 8px" }}>
                          {(r.case_numbers || []).map((cn) => cn.normalized || cn.raw).join(", ") || "—"}
                        </td>
                        <td style={{ padding: "10px 8px" }}>{r.hearing_date || "—"}</td>
                        <td style={{ padding: "10px 8px" }}>
                          <span
                            style={{
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontSize: "11px",
                              fontWeight: "600",
                              backgroundColor:
                                r.matter_status === "NEW_MATTER"
                                  ? "rgba(16, 185, 129, 0.15)"
                                  : "rgba(245, 158, 11, 0.15)",
                              color:
                                r.matter_status === "NEW_MATTER" ? "var(--success)" : "#f59e0b",
                            }}
                          >
                            {r.matter_status}
                          </span>
                        </td>
                        <td style={{ padding: "10px 8px", color: "var(--text-muted)", fontSize: "12px", maxWidth: "260px" }}>
                          {r.warnings && r.warnings.length > 0 ? r.warnings.join("; ") : "—"}
                        </td>
                        <td style={{ padding: "10px 8px" }}>
                          {currentOverride ? (
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <span
                                style={{
                                  fontSize: "11px",
                                  fontWeight: "600",
                                  color: "var(--accent)",
                                  backgroundColor: "rgba(99, 102, 241, 0.15)",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                }}
                              >
                                {currentOverride.action === "USE_EXISTING"
                                  ? "Using existing client"
                                  : "Importing anyway"}
                              </span>
                              <button
                                onClick={() => handleRemoveOverride(r.row_number)}
                                disabled={previewMutation.isPending}
                                style={{
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  border: "1px solid var(--border)",
                                  backgroundColor: "transparent",
                                  color: "var(--text-muted)",
                                  fontSize: "11px",
                                  cursor: "pointer",
                                }}
                                title="Reset override"
                              >
                                ✕ Reset
                              </button>
                            </div>
                          ) : isFlagged ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                              <button
                                onClick={() =>
                                  handleApplyOverride(r.row_number, { action: "CREATE_ANYWAY" })
                                }
                                disabled={previewMutation.isPending}
                                style={{
                                  padding: "4px 8px",
                                  borderRadius: "4px",
                                  backgroundColor: "var(--accent)",
                                  color: "#fff",
                                  border: "none",
                                  fontSize: "11px",
                                  fontWeight: "600",
                                  cursor: "pointer",
                                  textAlign: "left",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                Import anyway
                              </button>
                              {r.suggested_client_id && r.suggested_client_name && (
                                <button
                                  onClick={() =>
                                    handleApplyOverride(r.row_number, {
                                      action: "USE_EXISTING",
                                      client_id: r.suggested_client_id!,
                                    })
                                  }
                                  disabled={previewMutation.isPending}
                                  style={{
                                    padding: "4px 8px",
                                    borderRadius: "4px",
                                    backgroundColor: "rgba(255, 255, 255, 0.08)",
                                    color: "var(--text-primary)",
                                    border: "1px solid var(--border)",
                                    fontSize: "11px",
                                    fontWeight: "600",
                                    cursor: "pointer",
                                    textAlign: "left",
                                    whiteSpace: "nowrap",
                                  }}
                                >
                                  Use existing client {r.suggested_client_name}
                                </button>
                              )}
                            </div>
                          ) : (
                            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
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

              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
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
                    backgroundColor: commitMutation.isPending ? "var(--border)" : "var(--success)",
                    color: commitMutation.isPending ? "var(--text-muted)" : "#fff",
                    border: "none",
                    fontWeight: "700",
                    fontSize: "14px",
                    cursor: commitMutation.isPending ? "not-allowed" : "pointer",
                    opacity: commitMutation.isPending ? 0.7 : 1,
                  }}
                >
                  {commitMutation.isPending ? "Committing Import (this can take up to a minute)..." : "Commit Cases to Firm"}
                </button>
                {commitMutation.isPending && (
                  <div style={{ marginTop: "6px", fontSize: "12px", color: "var(--text-muted)", fontStyle: "italic" }}>
                    Hold on — this can take up to a minute.
                  </div>
                )}
              </div>
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
                {String(commitCounts.clients_created ?? 0)}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>MATTERS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String(commitCounts.matters_created ?? 0)}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>HEARINGS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String(commitCounts.hearings_created ?? 0)}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>CASE LINKS</div>
              <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>
                {String(commitCounts.case_links_created ?? 0)}
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
