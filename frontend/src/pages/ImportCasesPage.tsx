import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  uploadCaseImportFile,
  previewCaseImport,
  commitCaseImport,
  getImportTemplateUrl,
  type CaseImportUploadResponse,
  type CaseImportCommitResponse,
} from "../api/client";
import {
  PageHeader,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  EmptyState,
} from "../components/ui";

interface ImportCasesPageProps {
  onBack?: () => void;
  onViewMatters?: () => void;
}

interface RowOverride {
  action: "CREATE_NEW" | "USE_EXISTING" | "SKIP";
  target_client_id?: string;
  notes?: string;
}

interface ImportSummary {
  total_rows?: number;
  valid_rows_count?: number;
  flagged_rows_count?: number;
  skipped_rows_count?: number;
  new_clients_count?: number;
  existing_clients_count?: number;
  new_matters_count?: number;
  new_hearings_count?: number;
}

interface ImportPreviewRow {
  row_num: number;
  status: "VALID" | "FLAGGED" | "RESOLVED" | "SKIPPED";
  flags: string[];
  client_name?: string;
  matched_client_id?: string | null;
  matched_client_name?: string | null;
  matter_title?: string;
  case_number?: string;
  next_hearing_date?: string;
  client_override?: RowOverride | null;
}

interface CommitCounts {
  clients_created?: number;
  matters_created?: number;
  hearings_created?: number;
  tasks_created?: number;
  notes_created?: number;
}

export const ImportCasesPage: React.FC<ImportCasesPageProps> = ({ onBack, onViewMatters }) => {
  // 3 clear steps: 1: Upload, 2: Check, 3: Import
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<CaseImportUploadResponse | null>(null);
  const [commitResult, setCommitResult] = useState<CaseImportCommitResponse | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [mapping, setMapping] = useState<Record<string, number>>({});
  const [clientOverrides, setClientOverrides] = useState<Record<string, RowOverride>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const STANDARD_FIELDS: Array<{ key: string; label: string; required?: boolean }> = [
    { key: "client_name", label: "Client name", required: true },
    { key: "client_type", label: "Client type" },
    { key: "cin_or_pan", label: "CIN or PAN" },
    { key: "matter_title", label: "Matter title", required: true },
    { key: "case_type", label: "Case type" },
    { key: "court_or_forum", label: "Court or forum" },
    { key: "case_number", label: "Case number" },
    { key: "next_hearing_date", label: "Next hearing date" },
    { key: "lead_lawyer_email", label: "Lead lawyer email" },
    { key: "notes", label: "Notes" },
  ];

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadCaseImportFile(file),
    onSuccess: (data) => {
      setUploadResult(data);
      const initialMapping = data.mapping || {};
      setMapping(initialMapping);
      setClientOverrides({});
      const sheet = data.sheet_names && data.sheet_names.length > 0 ? data.sheet_names[0] : "";
      setSelectedSheet(sheet);
      setErrorMsg(null);

      // Automatically run preview check so user lands right on Check (step 2)
      previewMutation.mutate({
        overrides: {},
        currentMapping: initialMapping,
        importId: data.import_id,
        sheet,
      });
    },
    onError: (err: unknown) => {
      setErrorMsg(err instanceof Error ? err.message : "Failed to upload spreadsheet.");
    },
  });

  const previewMutation = useMutation({
    mutationFn: (args?: {
      overrides?: Record<string, RowOverride>;
      currentMapping?: Record<string, number>;
      importId?: string;
      sheet?: string;
    }) => {
      const id = args?.importId || uploadResult?.import_id;
      if (!id) throw new Error("No import in progress.");
      const currentOverrides = args?.overrides !== undefined ? args.overrides : clientOverrides;
      const m = args?.currentMapping !== undefined ? args.currentMapping : mapping;
      const s = args?.sheet !== undefined ? args.sheet : selectedSheet;
      return previewCaseImport(id, {
        mapping: m,
        client_overrides: currentOverrides,
        sheet_name: s || undefined,
      });
    },
    onSuccess: (data) => {
      setUploadResult(data);
      setErrorMsg(null);
      setStep(2);
    },
    onError: (err: unknown) => {
      setErrorMsg(err instanceof Error ? err.message : "Failed to check spreadsheet rows.");
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
      setStep(3);
    },
    onError: (err: unknown) => {
      setErrorMsg(err instanceof Error ? err.message : "Failed to commit import.");
    },
  });

  const handleApplyOverride = (rowNum: number, override: RowOverride) => {
    const nextOverrides = {
      ...clientOverrides,
      [String(rowNum)]: override,
    };
    setClientOverrides(nextOverrides);
    previewMutation.mutate({ overrides: nextOverrides });
  };

  const handleRemoveOverride = (rowNum: number) => {
    const nextOverrides = { ...clientOverrides };
    delete nextOverrides[String(rowNum)];
    setClientOverrides(nextOverrides);
    previewMutation.mutate({ overrides: nextOverrides });
  };

  const summary: ImportSummary =
    (uploadResult?.preview as { summary?: ImportSummary } | undefined)?.summary || {};
  const previewRows: ImportPreviewRow[] =
    (uploadResult?.preview as { rows?: ImportPreviewRow[] } | undefined)?.rows || [];
  const commitCounts: CommitCounts =
    (commitResult?.counts as CommitCounts | undefined) || {};

  // Group flagged rows at the top
  const flaggedRows = previewRows.filter(
    (r) => r.status === "FLAGGED" || r.status === "SKIPPED"
  );
  const readyRows = previewRows.filter(
    (r) => r.status === "VALID" || r.status === "RESOLVED"
  );

  return (
    <div>
      <PageHeader
        title="Import cases"
        description="Batch import cases, clients, and hearings from Excel or CSV"
        onBack={onBack}
      >
        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", fontSize: "var(--text-sm)" }}>
          <span style={{ fontWeight: step === 1 ? 600 : 400, color: step === 1 ? "var(--accent-main)" : "var(--text-muted)" }}>
            1. Upload
          </span>
          <span style={{ color: "var(--text-faint)" }}>→</span>
          <span style={{ fontWeight: step === 2 ? 600 : 400, color: step === 2 ? "var(--accent-main)" : "var(--text-muted)" }}>
            2. Check
          </span>
          <span style={{ color: "var(--text-faint)" }}>→</span>
          <span style={{ fontWeight: step === 3 ? 600 : 400, color: step === 3 ? "var(--status-done-text)" : "var(--text-muted)" }}>
            3. Import
          </span>
        </div>
      </PageHeader>

      {errorMsg && (
        <div
          style={{
            backgroundColor: "var(--status-overdue-bg)",
            border: "1px solid var(--status-overdue-border)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-2) var(--space-3)",
            color: "var(--status-overdue-text)",
            fontSize: "var(--text-sm)",
            marginBottom: "var(--space-4)",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Step 1: Upload */}
      {step === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "var(--space-3) var(--space-4)",
              backgroundColor: "var(--bg-subtle)",
              border: "1px solid var(--border-main)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <div>
              <div style={{ fontWeight: 500 }}>Download template</div>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                Pre-formatted spreadsheet with standard columns
              </div>
            </div>
            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <a
                href={getImportTemplateUrl("xlsx")}
                download="cases_import_template.xlsx"
                className="btn btn-secondary btn-sm"
              >
                Excel template (.xlsx)
              </a>
              <a
                href={getImportTemplateUrl("csv")}
                download="cases_import_template.csv"
                className="btn btn-secondary btn-sm"
              >
                CSV template (.csv)
              </a>
            </div>
          </div>

          <div
            style={{
              padding: "var(--space-8)",
              border: "1px dashed var(--border-main)",
              borderRadius: "var(--radius-lg)",
              backgroundColor: "var(--bg-app)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "var(--space-4)",
              textAlign: "center",
            }}
          >
            <div>
              <p style={{ fontWeight: 500, marginBottom: "var(--space-1)" }}>
                Select a spreadsheet to import
              </p>
              <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                Supported formats: Excel (.xlsx) and CSV (.csv), up to 10 MB
              </p>
            </div>

            <input
              type="file"
              accept=".xlsx,.csv"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
              style={{ fontSize: "var(--text-sm)" }}
            />

            <Button
              variant="primary"
              onClick={() => {
                if (selectedFile) uploadMutation.mutate(selectedFile);
              }}
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Uploading and checking..." : "Upload and check"}
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Check (Mapping & Grouped Rows Preview) */}
      {step === 2 && uploadResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          {/* Summary band */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "var(--space-3) var(--space-4)",
              backgroundColor: "var(--bg-subtle)",
              border: "1px solid var(--border-main)",
              borderRadius: "var(--radius-md)",
              flexWrap: "wrap",
              gap: "var(--space-3)",
            }}
          >
            <div style={{ display: "flex", gap: "var(--space-4)", fontSize: "var(--text-sm)" }}>
              <span>Total rows: <strong>{summary.total_rows ?? previewRows.length}</strong></span>
              <span>Ready: <strong style={{ color: "var(--status-done-text)" }}>{summary.valid_rows_count ?? readyRows.length}</strong></span>
              {flaggedRows.length > 0 && (
                <span>Flagged: <strong style={{ color: "var(--status-overdue-text)" }}>{summary.flagged_rows_count ?? flaggedRows.length}</strong></span>
              )}
            </div>

            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <Button variant="secondary" size="sm" onClick={() => setStep(1)}>
                Choose another file
              </Button>
              <Button
                variant="primary"
                onClick={() => commitMutation.mutate()}
                disabled={commitMutation.isPending}
              >
                {commitMutation.isPending ? "Importing..." : "Confirm and import"}
              </Button>
            </div>
          </div>

          {/* Column mapping drawer / table */}
          <div>
            <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, marginBottom: "var(--space-2)" }}>
              Column mapping
            </h2>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                gap: "var(--space-2)",
                padding: "var(--space-3)",
                backgroundColor: "var(--bg-subtle)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-main)",
              }}
            >
              {STANDARD_FIELDS.map((field) => (
                <div key={field.key} style={{ fontSize: "var(--text-sm)" }}>
                  <span style={{ color: "var(--text-muted)" }}>{field.label}: </span>
                  <span style={{ fontWeight: 500 }}>
                    {typeof mapping[field.key] === "number" && uploadResult.headers
                      ? uploadResult.headers[mapping[field.key]]
                      : "Unmapped"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Group 1: Flagged rows grouped at top */}
          {flaggedRows.length > 0 && (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
                <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, color: "var(--status-overdue-text)" }}>
                  Flagged rows requiring attention ({flaggedRows.length})
                </h2>
                <Badge variant="overdue">Review</Badge>
              </div>

              <Table>
                <Thead>
                  <Tr>
                    <Th style={{ width: "50px" }}>Row</Th>
                    <Th>Status</Th>
                    <Th>Client name</Th>
                    <Th>Matter title</Th>
                    <Th>Flag reason</Th>
                    <Th style={{ width: "220px" }}>Action</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {flaggedRows.map((row) => (
                    <Tr key={row.row_num}>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                        {row.row_num}
                      </Td>
                      <Td>
                        <Badge variant="overdue">Flagged</Badge>
                      </Td>
                      <Td style={{ fontWeight: 500 }}>{row.client_name || "—"}</Td>
                      <Td>{row.matter_title || "—"}</Td>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--status-overdue-text)" }}>
                        {row.flags?.join("; ") || "Check row"}
                      </Td>
                      <Td>
                        <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "wrap" }}>
                          {row.client_override ? (
                            <Button
                              variant="quiet"
                              size="sm"
                              onClick={() => handleRemoveOverride(row.row_num)}
                            >
                              Reset
                            </Button>
                          ) : (
                            <>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() =>
                                  handleApplyOverride(row.row_num, { action: "CREATE_NEW" })
                                }
                              >
                                Import anyway
                              </Button>
                              {row.matched_client_id && (
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  onClick={() =>
                                    handleApplyOverride(row.row_num, {
                                      action: "USE_EXISTING",
                                      target_client_id: row.matched_client_id || undefined,
                                    })
                                  }
                                >
                                  Use existing
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </div>
          )}

          {/* Group 2: Ready rows */}
          <div>
            <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, marginBottom: "var(--space-2)" }}>
              Ready to import ({readyRows.length})
            </h2>

            {readyRows.length === 0 ? (
              <EmptyState message="No valid rows ready for import." />
            ) : (
              <Table>
                <Thead>
                  <Tr>
                    <Th style={{ width: "50px" }}>Row</Th>
                    <Th>Status</Th>
                    <Th>Client name</Th>
                    <Th>Matter title</Th>
                    <Th>Case number</Th>
                    <Th>Next hearing</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {readyRows.slice(0, 50).map((row) => (
                    <Tr key={row.row_num}>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                        {row.row_num}
                      </Td>
                      <Td>
                        <Badge variant="done">Ready</Badge>
                      </Td>
                      <Td style={{ fontWeight: 500 }}>{row.client_name || "—"}</Td>
                      <Td>{row.matter_title || "—"}</Td>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                        {row.case_number || "—"}
                      </Td>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                        {row.next_hearing_date || "—"}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Complete / Results */}
      {step === 3 && commitResult && (
        <div
          style={{
            padding: "var(--space-8)",
            border: "1px solid var(--border-main)",
            borderRadius: "var(--radius-lg)",
            backgroundColor: "var(--bg-app)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-4)",
          }}
        >
          <div>
            <Badge variant="done">Import completed</Badge>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: 600, marginTop: "var(--space-2)" }}>
              Cases imported successfully
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "var(--text-base)", marginTop: "var(--space-1)" }}>
              The records have been added to your firm vault and indexed.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              gap: "var(--space-3)",
              padding: "var(--space-4)",
              backgroundColor: "var(--bg-subtle)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-main)",
            }}
          >
            <div>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Clients created</div>
              <div style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>
                {commitCounts.clients_created ?? 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Matters created</div>
              <div style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>
                {commitCounts.matters_created ?? 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Hearings scheduled</div>
              <div style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>
                {commitCounts.hearings_created ?? 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Tasks created</div>
              <div style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>
                {commitCounts.tasks_created ?? 0}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
            <Button
              variant="primary"
              onClick={() => {
                if (onViewMatters) onViewMatters();
                else if (onBack) onBack();
              }}
            >
              View matters
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setStep(1);
                setSelectedFile(null);
                setUploadResult(null);
                setCommitResult(null);
                setClientOverrides({});
              }}
            >
              Import another file
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
