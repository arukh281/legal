import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMatter,
  fetchMatterDocuments,
  fetchDocumentVersions,
  addCaseLink,
  removeCaseLink,
  uploadDocument,
  getDocumentDownloadUrl,
  type PdocResponse,
  type PdocVersionResponse,
  type CaseLinkCreateRequest,
} from "../api/client";
import { SourceViewer } from "../components/SourceViewer";

interface MatterDetailPageProps {
  matterId: string;
  onBack: () => void;
  onSelectClient?: (clientId: string) => void;
}

export const MatterDetailPage: React.FC<MatterDetailPageProps> = ({
  matterId,
  onBack,
  onSelectClient,
}) => {
  const queryClient = useQueryClient();

  // Modal and viewer states
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [versionTargetPdocId, setVersionTargetPdocId] = useState<string | null>(null);
  const [expandedVersionsDocId, setExpandedVersionsDocId] = useState<string | null>(null);

  // Source viewer target
  const [viewingPdoc, setViewingPdoc] = useState<{ pdocId: string; pver: string } | null>(null);

  // Case link form
  const [showCaseLinkForm, setShowCaseLinkForm] = useState(false);
  const [caseScheme, setCaseScheme] = useState("CASE_NO");
  const [caseValue, setCaseValue] = useState("");

  // Upload form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [stage, setStage] = useState("ORDER");
  const [provenanceChoice, setProvenanceChoice] = useState<"COURT" | "CLIENT" | "FIRM" | "OPPONENT" | "THIRD_PARTY">("COURT");
  const [docType, setDocType] = useState("ORDER");
  const [docTitle, setDocTitle] = useState("");

  const { data: matterData, isLoading: matterLoading } = useQuery({
    queryKey: ["matter", matterId],
    queryFn: () => fetchMatter(matterId),
  });

  const { data: documents, isLoading: docsLoading } = useQuery({
    queryKey: ["matter_documents", matterId],
    queryFn: () => fetchMatterDocuments(matterId),
  });

  const { data: versionsData } = useQuery({
    queryKey: ["doc_versions", expandedVersionsDocId],
    queryFn: () => (expandedVersionsDocId ? fetchDocumentVersions(expandedVersionsDocId) : Promise.resolve([])),
    enabled: Boolean(expandedVersionsDocId),
  });

  // Mutations
  const addCaseMutation = useMutation({
    mutationFn: (req: CaseLinkCreateRequest) => addCaseLink(matterId, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
      setShowCaseLinkForm(false);
      setCaseValue("");
    },
  });

  const removeCaseMutation = useMutation({
    mutationFn: ({ scheme, val }: { scheme: string; val: string }) =>
      removeCaseLink(matterId, scheme, val),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => uploadDocument(matterId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter_documents", matterId] });
      queryClient.invalidateQueries({ queryKey: ["doc_versions", versionTargetPdocId] });
      setShowUploadModal(false);
      resetUploadForm();
    },
  });

  const resetUploadForm = () => {
    setSelectedFile(null);
    setVersionTargetPdocId(null);
    setDocTitle("");
    setStage("ORDER");
    setProvenanceChoice("COURT");
    setDocType("ORDER");
  };

  const provenanceConfig = {
    COURT: {
      label: "Court record / order",
      icon: "🏛️",
      trust: "TENANT_COURT_RECORD",
      privilege: "UNPRIVILEGED",
      defaultStage: "ORDER",
      defaultDocType: "ORDER",
    },
    CLIENT: {
      label: "Client document",
      icon: "🏢",
      trust: "TENANT_CLIENT_DOC",
      privilege: "ATTORNEY_CLIENT",
      defaultStage: "EVIDENCE",
      defaultDocType: "DOCUMENT",
    },
    FIRM: {
      label: "Internal draft / work product",
      icon: "⚖️",
      trust: "TENANT_WORK_PRODUCT",
      privilege: "ATTORNEY_CLIENT",
      defaultStage: "DRAFT",
      defaultDocType: "DRAFT",
    },
    OPPONENT: {
      label: "Opposing document",
      icon: "🛡️",
      trust: "TENANT_OPPOSING_DOC",
      privilege: "UNPRIVILEGED",
      defaultStage: "REPLY",
      defaultDocType: "PLEADING",
    },
    THIRD_PARTY: {
      label: "Third party record",
      icon: "📄",
      trust: "TENANT_CORRESPONDENCE",
      privilege: "UNPRIVILEGED",
      defaultStage: "CORRESPONDENCE",
      defaultDocType: "CORRESPONDENCE",
    },
  };

  const handleProvenanceSelect = (choice: "COURT" | "CLIENT" | "FIRM" | "OPPONENT" | "THIRD_PARTY") => {
    setProvenanceChoice(choice);
    const cfg = provenanceConfig[choice];
    setStage(cfg.defaultStage);
    setDocType(cfg.defaultDocType);
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    const cfg = provenanceConfig[provenanceChoice];
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("stage", stage);
    formData.append("provenance", provenanceChoice);
    formData.append("trust_label", cfg.trust);
    formData.append("privilege_class", cfg.privilege);
    formData.append("doc_type", docType);
    if (docTitle.trim()) {
      formData.append("title", docTitle.trim());
    }
    if (versionTargetPdocId) {
      formData.append("pdoc_id", versionTargetPdocId);
    }

    uploadMutation.mutate(formData);
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      if (!docTitle) setDocTitle(file.name);
    }
  };

  if (matterLoading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading matter workspace...</div>;
  }

  if (!matterData) {
    return (
      <div style={{ padding: "20px" }}>
        <button onClick={onBack}>← Back</button>
        <div style={{ color: "var(--danger)", marginTop: "16px" }}>Matter not found or access denied.</div>
      </div>
    );
  }

  const { matter, client, case_links } = matterData;

  // Group documents by stage
  const stagesOrder = ["NOTICE", "PLEADING", "REPLY", "ORDER", "CORRESPONDENCE", "EVIDENCE", "DRAFT", "OTHER"];
  const docsByStage: Record<string, PdocResponse[]> = {};
  for (const s of stagesOrder) {
    docsByStage[s] = [];
  }
  for (const doc of documents || []) {
    const s = doc.stage in docsByStage ? doc.stage : "OTHER";
    docsByStage[s].push(doc);
  }

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "16px" }}>
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "none",
          color: "var(--accent)",
          fontSize: "14px",
          cursor: "pointer",
          padding: 0,
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        ← Back to Matters
      </button>

      {/* Matter Header Card */}
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          marginBottom: "28px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "12px",
            marginBottom: "16px",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <h1 style={{ fontSize: "22px", fontWeight: "700", margin: 0 }}>
                {matter.title}
              </h1>
              {matter.status === "CLOSED" ? (
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "600",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    backgroundColor: "#f3f4f6",
                    color: "#4b5563",
                  }}
                >
                  Closed
                </span>
              ) : (
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "600",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    backgroundColor: "#ecfdf5",
                    color: "#065f46",
                  }}
                >
                  Active
                </span>
              )}
            </div>

            {/* Client link */}
            {client && (
              <div style={{ marginTop: "6px", fontSize: "14px" }}>
                <span style={{ color: "var(--text-muted)" }}>Client: </span>
                <span
                  onClick={() => onSelectClient && onSelectClient(client.client_id)}
                  style={{
                    color: "var(--accent)",
                    fontWeight: "600",
                    cursor: onSelectClient ? "pointer" : "default",
                  }}
                >
                  {client.display_name}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => {
              resetUploadForm();
              setShowUploadModal(true);
            }}
            style={{
              backgroundColor: "var(--accent)",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              padding: "10px 18px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            + Upload Document
          </button>
        </div>

        {/* Matter Attributes */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "16px",
            borderTop: "1px solid var(--border)",
            paddingTop: "16px",
            fontSize: "13px",
          }}
        >
          <div>
            <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px" }}>
              CASE TYPE
            </span>
            <span style={{ fontWeight: "600" }}>{matter.case_type || "General dispute"}</span>
          </div>

          <div>
            <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px" }}>
              COURT / FORUM
            </span>
            <span style={{ fontWeight: "600" }}>{matter.court_or_forum || "Not specified"}</span>
          </div>

          <div>
            <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px" }}>
              CLIENT ROLE
            </span>
            <span>{matter.client_role}</span>
          </div>
        </div>

        {/* Case Numbers Section */}
        <div style={{ borderTop: "1px solid var(--border)", marginTop: "16px", paddingTop: "14px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-muted)" }}>
              CASE NUMBERS
            </span>
            <button
              onClick={() => setShowCaseLinkForm(!showCaseLinkForm)}
              style={{
                background: "none",
                border: "none",
                color: "var(--accent)",
                fontSize: "12px",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              {showCaseLinkForm ? "Cancel" : "+ Add Case Number"}
            </button>
          </div>

          {/* Add case form */}
          {showCaseLinkForm && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (caseValue.trim()) {
                  addCaseMutation.mutate({
                    scheme: caseScheme,
                    value_normalized: caseValue.trim(),
                    role: "CASE",
                    track: true,
                  });
                }
              }}
              style={{
                display: "flex",
                gap: "8px",
                marginBottom: "12px",
                flexWrap: "wrap",
              }}
            >
              <input
                type="text"
                placeholder="Scheme (e.g. CASE_NO, CNR)"
                value={caseScheme}
                onChange={(e) => setCaseScheme(e.target.value)}
                style={{
                  width: "120px",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  fontSize: "12px",
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                }}
              />
              <input
                type="text"
                required
                placeholder="Case number e.g. CP (IB) 123/MB/2026"
                value={caseValue}
                onChange={(e) => setCaseValue(e.target.value)}
                style={{
                  flex: 1,
                  minWidth: "200px",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  fontSize: "12px",
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                }}
              />
              <button
                type="submit"
                disabled={addCaseMutation.isPending}
                style={{
                  padding: "6px 14px",
                  backgroundColor: "var(--accent)",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Save
              </button>
            </form>
          )}

          {/* Case numbers list */}
          {case_links.length === 0 ? (
            <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
              No case numbers added yet.
            </span>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {case_links.map((cl) => (
                <span
                  key={`${cl.scheme}:${cl.value_normalized}`}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    backgroundColor: "var(--bg-tertiary)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    padding: "4px 8px",
                    fontSize: "12px",
                    fontWeight: "500",
                  }}
                >
                  <span style={{ color: "var(--text-muted)", fontSize: "10px" }}>{cl.scheme}:</span>
                  <span>{cl.value_normalized}</span>
                  <button
                    onClick={() => removeCaseMutation.mutate({ scheme: cl.scheme, val: cl.value_normalized })}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                      padding: "0 2px",
                      fontSize: "12px",
                    }}
                    title="Remove case number"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Document Vault Section */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Documents</h2>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "2px 0 0" }}>
              Case files grouped by procedural stage
            </p>
          </div>
          <button
            onClick={() => {
              resetUploadForm();
              setShowUploadModal(true);
            }}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              background: "none",
              fontSize: "13px",
              fontWeight: "500",
              cursor: "pointer",
            }}
          >
            + Upload
          </button>
        </div>

        {docsLoading ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
            Loading vault documents...
          </div>
        ) : (!documents || documents.length === 0) ? (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            style={{
              padding: "48px 24px",
              textAlign: "center",
              backgroundColor: "var(--bg-secondary)",
              border: "2px dashed var(--border)",
              borderRadius: "12px",
            }}
          >
            <p style={{ fontSize: "16px", fontWeight: "600", marginBottom: "6px" }}>
              Document Vault is Empty
            </p>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "16px" }}>
              Drag and drop PDF, DOCX, EML, or ZIP files here, or click upload.
            </p>
            <button
              onClick={() => {
                resetUploadForm();
                setShowUploadModal(true);
              }}
              style={{
                backgroundColor: "var(--accent)",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                padding: "8px 16px",
                fontSize: "13px",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              Upload Document
            </button>
          </div>
        ) : (
          <div style={{ display: "grid", gap: "20px" }}>
            {stagesOrder.map((stageKey) => {
              const stageDocs = docsByStage[stageKey];
              if (stageDocs.length === 0) return null;

              return (
                <div key={stageKey}>
                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: "700",
                      letterSpacing: "0.04em",
                      color: "var(--text-muted)",
                      marginBottom: "8px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    <span>{stageKey}</span>
                    <span style={{ fontSize: "11px", opacity: 0.7 }}>({stageDocs.length})</span>
                  </div>

                  <div style={{ display: "grid", gap: "8px" }}>
                    {stageDocs.map((doc) => (
                      <div
                        key={doc.pdoc_id}
                        style={{
                          backgroundColor: "var(--bg-secondary)",
                          border: "1px solid var(--border)",
                          borderRadius: "8px",
                          padding: "14px 16px",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            flexWrap: "wrap",
                            gap: "10px",
                          }}
                        >
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                              <span style={{ fontWeight: "600", fontSize: "14px" }}>
                                {doc.title || doc.pdoc_id}
                              </span>
                              <span
                                style={{
                                  fontSize: "11px",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  backgroundColor: "var(--bg-tertiary)",
                                  color: "var(--text-secondary)",
                                  fontWeight: "600",
                                }}
                              >
                                {doc.current_version || "v1"}
                              </span>
                              <span
                                style={{
                                  fontSize: "11px",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  backgroundColor: "var(--bg-tertiary)",
                                  color: "var(--text-muted)",
                                }}
                              >
                                {doc.provenance}
                              </span>
                              {doc.family_id && (
                                <span
                                  style={{
                                    fontSize: "10px",
                                    padding: "2px 6px",
                                    borderRadius: "4px",
                                    backgroundColor: "#ede9fe",
                                    color: "#5b21b6",
                                  }}
                                  title="Expanded from ZIP batch"
                                >
                                  ZIP Batch
                                </span>
                              )}
                            </div>

                            <div
                              style={{
                                fontSize: "12px",
                                color: "var(--text-muted)",
                                marginTop: "4px",
                                display: "flex",
                                gap: "12px",
                              }}
                            >
                              <span>Type: {doc.doc_type}</span>
                              <span>Added: {new Date(doc.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>

                          {/* Actions */}
                          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                            <button
                              onClick={() =>
                                setViewingPdoc({
                                  pdocId: doc.pdoc_id,
                                  pver: doc.current_version || "v1",
                                })
                              }
                              style={{
                                padding: "6px 12px",
                                backgroundColor: "var(--accent)",
                                color: "#fff",
                                border: "none",
                                borderRadius: "6px",
                                fontSize: "12px",
                                fontWeight: "600",
                                cursor: "pointer",
                              }}
                            >
                              Open Viewer
                            </button>

                            <a
                              href={getDocumentDownloadUrl(doc.pdoc_id, doc.current_version || undefined)}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                padding: "6px 10px",
                                backgroundColor: "var(--bg-tertiary)",
                                color: "var(--text-primary)",
                                border: "1px solid var(--border)",
                                borderRadius: "6px",
                                fontSize: "12px",
                                textDecoration: "none",
                                fontWeight: "500",
                              }}
                            >
                              Download
                            </a>

                            <button
                              onClick={() => {
                                setVersionTargetPdocId(doc.pdoc_id);
                                setDocTitle(doc.title || "");
                                setStage(doc.stage);
                                setShowUploadModal(true);
                              }}
                              style={{
                                padding: "6px 10px",
                                backgroundColor: "transparent",
                                color: "var(--text-secondary)",
                                border: "1px solid var(--border)",
                                borderRadius: "6px",
                                fontSize: "12px",
                                cursor: "pointer",
                              }}
                              title="Upload updated version"
                            >
                              + New Version
                            </button>

                            <button
                              onClick={() => {
                                setExpandedVersionsDocId(
                                  expandedVersionsDocId === doc.pdoc_id ? null : doc.pdoc_id
                                );
                              }}
                              style={{
                                padding: "6px 8px",
                                backgroundColor: "transparent",
                                color: "var(--text-muted)",
                                border: "none",
                                fontSize: "12px",
                                cursor: "pointer",
                              }}
                            >
                              {expandedVersionsDocId === doc.pdoc_id ? "Hide History ▲" : "History ▼"}
                            </button>
                          </div>
                        </div>

                        {/* Version History Drawer */}
                        {expandedVersionsDocId === doc.pdoc_id && (
                          <div
                            style={{
                              marginTop: "12px",
                              paddingTop: "12px",
                              borderTop: "1px solid var(--border)",
                              backgroundColor: "var(--bg-primary)",
                              borderRadius: "6px",
                              padding: "10px",
                            }}
                          >
                            <span style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)" }}>
                              VERSION HISTORY
                            </span>
                            <div style={{ display: "grid", gap: "6px", marginTop: "6px" }}>
                              {(versionsData || []).map((v: PdocVersionResponse) => (
                                <div
                                  key={v.pver}
                                  style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    fontSize: "12px",
                                    padding: "4px 8px",
                                    borderRadius: "4px",
                                    backgroundColor: "var(--bg-secondary)",
                                  }}
                                >
                                  <div>
                                    <span style={{ fontWeight: "600", marginRight: "8px" }}>{v.pver}</span>
                                    <span style={{ color: "var(--text-muted)", fontSize: "11px", marginRight: "8px" }}>
                                      SHA: {v.raw_sha256.slice(0, 10)}...
                                    </span>
                                    {v.gate === "FLAGGED" && (
                                      <span
                                        style={{
                                          fontSize: "10px",
                                          padding: "1px 6px",
                                          borderRadius: "4px",
                                          backgroundColor: "#fee2e2",
                                          color: "#991b1b",
                                          fontWeight: "600",
                                        }}
                                      >
                                        FLAGGED (Hidden text)
                                      </span>
                                    )}
                                  </div>
                                  <div style={{ display: "flex", gap: "8px" }}>
                                    <button
                                      onClick={() => setViewingPdoc({ pdocId: doc.pdoc_id, pver: v.pver })}
                                      style={{
                                        background: "none",
                                        border: "none",
                                        color: "var(--accent)",
                                        cursor: "pointer",
                                        fontSize: "11px",
                                        fontWeight: "600",
                                      }}
                                    >
                                      View
                                    </button>
                                    <a
                                      href={getDocumentDownloadUrl(doc.pdoc_id, v.pver)}
                                      target="_blank"
                                      rel="noreferrer"
                                      style={{
                                        color: "var(--text-secondary)",
                                        fontSize: "11px",
                                        textDecoration: "none",
                                      }}
                                    >
                                      Download
                                    </a>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "16px",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              padding: "24px",
              width: "100%",
              maxWidth: "560px",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>
                {versionTargetPdocId ? "Upload New Version" : "Upload Document"}
              </h2>
              <button
                onClick={() => setShowUploadModal(false)}
                style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUploadSubmit}>
              {/* File input / Drag zone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                style={{
                  border: "2px dashed var(--border)",
                  borderRadius: "8px",
                  padding: "20px",
                  textAlign: "center",
                  backgroundColor: "var(--bg-secondary)",
                  marginBottom: "16px",
                }}
              >
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.eml,.zip"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      const file = e.target.files[0];
                      setSelectedFile(file);
                      if (!docTitle) setDocTitle(file.name);
                    }
                  }}
                  style={{ display: "block", margin: "0 auto 8px" }}
                />
                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                  Accepted formats: PDF (scanned & digital), DOCX, EML, ZIP
                </span>
                {selectedFile && (
                  <div style={{ marginTop: "8px", fontWeight: "600", fontSize: "13px", color: "var(--accent)" }}>
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </div>
                )}
              </div>

              {/* Title */}
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Document Title (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Petition under Section 9 IBC"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-secondary)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>

              {/* Stage tag selection */}
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px" }}>
                  Procedural Stage
                </label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {stagesOrder.map((s) => (
                    <button
                      type="button"
                      key={s}
                      onClick={() => setStage(s)}
                      style={{
                        padding: "6px 10px",
                        fontSize: "12px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        backgroundColor: stage === s ? "var(--accent)" : "var(--bg-secondary)",
                        color: stage === s ? "#fff" : "var(--text-secondary)",
                        cursor: "pointer",
                        fontWeight: stage === s ? "600" : "500",
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* One-click Provenance Choices */}
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px" }}>
                  Provenance & Trust (One-Click)
                </label>
                <div style={{ display: "grid", gap: "8px" }}>
                  {(["COURT", "CLIENT", "FIRM", "OPPONENT", "THIRD_PARTY"] as const).map((key) => {
                    const cfg = provenanceConfig[key];
                    const active = provenanceChoice === key;
                    return (
                      <div
                        key={key}
                        onClick={() => handleProvenanceSelect(key)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          padding: "10px 12px",
                          borderRadius: "8px",
                          border: active ? "2px solid var(--accent)" : "1px solid var(--border)",
                          backgroundColor: active ? "var(--bg-tertiary)" : "var(--bg-secondary)",
                          cursor: "pointer",
                        }}
                      >
                        <span style={{ fontSize: "18px" }}>{cfg.icon}</span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: "13px", fontWeight: "600" }}>{cfg.label}</div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                            Trust: {cfg.trust} • Privilege: {cfg.privilege}
                          </div>
                        </div>
                        {active && <span style={{ color: "var(--accent)", fontWeight: "700" }}>✓</span>}
                      </div>
                    );
                  })}
                </div>
              </div>

              {uploadMutation.isError && (
                <div style={{ color: "var(--danger)", fontSize: "13px", marginBottom: "12px" }}>
                  Upload error: {(uploadMutation.error as Error).message}
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  style={{
                    padding: "8px 14px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    background: "none",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploadMutation.isPending || !selectedFile}
                  style={{
                    padding: "8px 18px",
                    borderRadius: "6px",
                    border: "none",
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {uploadMutation.isPending ? "Ingesting & Parsing..." : "Upload & Parse"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Private Document Source Viewer */}
      {viewingPdoc && (
        <SourceViewer
          anchorId={`${viewingPdoc.pdocId}/${viewingPdoc.pver}#p1`}
          pdocId={viewingPdoc.pdocId}
          pver={viewingPdoc.pver}
          onClose={() => setViewingPdoc(null)}
        />
      )}
    </div>
  );
};
