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
  fetchMatterHearings,
  createMatterHearing,
  recordHearingOutcome,
  fetchMatterDeadlines,
  createMatterDeadline,
  updateDeadlineLifecycle,
  fetchMatterOrders,
  fetchMatterTimeline,
  fetchMatterTasks,
  fetchMatterClientUpdates,
  createMatterTask,
  fetchMatterMembers,
  getMatterCalendarExportUrl,
  type PdocResponse,
  type PdocVersionResponse,
  type CaseLinkCreateRequest,
  type HearingResponse,
  type CourtOrderResponse,
} from "../api/client";
import { SourceViewer } from "../components/SourceViewer";
import { TasksTab } from "../components/TasksTab";
import { ClientUpdatesTab } from "../components/ClientUpdatesTab";
import { ShareLinkModal } from "../components/ShareLinkModal";

interface MatterDetailPageProps {
  matterId: string;
  onBack: () => void;
  onSelectClient?: (clientId: string) => void;
}

export type MatterTab =
  | "documents"
  | "hearings"
  | "dates"
  | "tasks"
  | "client_updates"
  | "orders"
  | "timeline";

function getPreviousWorkingDay(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() - 1);
  if (d.getDay() === 0) {
    d.setDate(d.getDate() - 2);
  } else if (d.getDay() === 6) {
    d.setDate(d.getDate() - 1);
  }
  return d.toISOString().split("T")[0];
}

export const MatterDetailPage: React.FC<MatterDetailPageProps> = ({
  matterId,
  onBack,
  onSelectClient,
}) => {
  const queryClient = useQueryClient();

  // Tab state
  const [activeTab, setActiveTab] = useState<MatterTab>("documents");

  // Modal and viewer states
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [versionTargetPdocId, setVersionTargetPdocId] = useState<string | null>(null);
  const [expandedVersionsDocId, setExpandedVersionsDocId] = useState<string | null>(null);

  // Source viewer target
  const [viewingPdoc, setViewingPdoc] = useState<{ pdocId: string; pver: string } | null>(null);
  const [viewingPublicOrder, setViewingPublicOrder] = useState<CourtOrderResponse | null>(null);

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

  // Hearing form & outcome modal state
  const [showHearingForm, setShowHearingForm] = useState(false);
  const [hearingDate, setHearingDate] = useState("");
  const [hearingCourtNo, setHearingCourtNo] = useState("");
  const [hearingItemNo, setHearingItemNo] = useState("");
  const [hearingBench, setHearingBench] = useState("");
  const [hearingPurpose, setHearingPurpose] = useState("");
  const [outcomeHearing, setOutcomeHearing] = useState<HearingResponse | null>(null);
  const [outcomeText, setOutcomeText] = useState("");
  const [outcomeStatus, setOutcomeStatus] = useState("HEARD");
  const [nextHearingDate, setNextHearingDate] = useState("");
  const [nextHearingPurpose, setNextHearingPurpose] = useState("");

  // Deadline form state
  const [showDeadlineForm, setShowDeadlineForm] = useState(false);
  const [deadlineLabel, setDeadlineLabel] = useState("");
  const [deadlineDueOn, setDeadlineDueOn] = useState("");
  const [deadlineOwner, setDeadlineOwner] = useState("");

  // R3: Share link modal state
  const [showShareLinkModal, setShowShareLinkModal] = useState(false);

  // R3: Hearing outcome task creation state
  const [createTaskForNextDate, setCreateTaskForNextDate] = useState(false);
  const [nextDateTaskTitle, setNextDateTaskTitle] = useState("");
  const [nextDateTaskDueOn, setNextDateTaskDueOn] = useState("");
  const [nextDateTaskAssignee, setNextDateTaskAssignee] = useState("");

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

  const { data: hearings, isLoading: hearingsLoading } = useQuery({
    queryKey: ["matter_hearings", matterId],
    queryFn: () => fetchMatterHearings(matterId),
  });

  const { data: deadlines, isLoading: deadlinesLoading } = useQuery({
    queryKey: ["matter_deadlines", matterId],
    queryFn: () => fetchMatterDeadlines(matterId),
  });

  const { data: orders, isLoading: ordersLoading } = useQuery({
    queryKey: ["matter_orders", matterId],
    queryFn: () => fetchMatterOrders(matterId),
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ["matter_timeline", matterId],
    queryFn: () => fetchMatterTimeline(matterId),
  });

  const { data: tasks } = useQuery({
    queryKey: ["matter_tasks", matterId],
    queryFn: () => fetchMatterTasks(matterId),
  });

  const { data: clientUpdates } = useQuery({
    queryKey: ["matter_client_updates", matterId],
    queryFn: () => fetchMatterClientUpdates(matterId),
  });

  const { data: members = [] } = useQuery({
    queryKey: ["matter_members", matterId],
    queryFn: () => fetchMatterMembers(matterId),
  });

  const assignableMembers = members.filter((m) => m.role === "LEAD" || m.role === "MEMBER");

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
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
      setShowUploadModal(false);
      resetUploadForm();
    },
  });

  const createHearingMutation = useMutation({
    mutationFn: (payload: { date: string; court_no?: string; item_no?: string; bench?: string; purpose?: string }) =>
      createMatterHearing(matterId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter_hearings", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
      setShowHearingForm(false);
      setHearingDate("");
      setHearingCourtNo("");
      setHearingItemNo("");
      setHearingBench("");
      setHearingPurpose("");
    },
  });

  const recordOutcomeMutation = useMutation({
    mutationFn: ({
      hearingId,
      outcome,
      status,
      next_date,
      next_purpose,
    }: {
      hearingId: string;
      outcome: string;
      status: string;
      next_date?: string;
      next_purpose?: string;
    }) =>
      recordHearingOutcome(hearingId, {
        outcome,
        status,
        next_date: next_date || null,
        next_purpose: next_purpose || null,
      }),
    onSuccess: () => {
      if (createTaskForNextDate && nextHearingDate && nextDateTaskAssignee && nextDateTaskTitle) {
        createMatterTask(matterId, {
          title: nextDateTaskTitle.trim(),
          due_on: nextDateTaskDueOn || undefined,
          assignee: nextDateTaskAssignee,
          hearing_id: outcomeHearing?.hearing_id,
        }).then(() => {
          queryClient.invalidateQueries({ queryKey: ["matter_tasks", matterId] });
          queryClient.invalidateQueries({ queryKey: ["today"] });
        });
      }
      queryClient.invalidateQueries({ queryKey: ["matter_hearings", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
      setOutcomeHearing(null);
      setOutcomeText("");
      setNextHearingDate("");
      setNextHearingPurpose("");
      setCreateTaskForNextDate(false);
      setNextDateTaskTitle("");
      setNextDateTaskDueOn("");
      setNextDateTaskAssignee("");
    },
  });

  const createDeadlineMutation = useMutation({
    mutationFn: (payload: { label: string; due_on: string; owner?: string }) =>
      createMatterDeadline(matterId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter_deadlines", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
      setShowDeadlineForm(false);
      setDeadlineLabel("");
      setDeadlineDueOn("");
      setDeadlineOwner("");
    },
  });

  const updateDeadlineMutation = useMutation({
    mutationFn: ({ deadlineId, lifecycle }: { deadlineId: string; lifecycle: string }) =>
      updateDeadlineLifecycle(deadlineId, lifecycle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter_deadlines", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
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

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <button
              onClick={() => setShowShareLinkModal(true)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "10px 14px",
                fontSize: "13px",
                fontWeight: "600",
                color: "var(--text-primary)",
                cursor: "pointer",
              }}
            >
              <span>🔗</span> Share Link
            </button>
            <a
              href={getMatterCalendarExportUrl(matterId)}
              download={`matter_${matterId}_calendar.ics`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "10px 14px",
                fontSize: "13px",
                fontWeight: "600",
                color: "var(--text-primary)",
                textDecoration: "none",
                cursor: "pointer",
              }}
            >
              <span>📅</span> Export Calendar (.ics)
            </a>
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
            <span>{matter.client_role === "NOT_SET" ? "Not set" : matter.client_role}</span>
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

      {/* Navigation Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border)", marginBottom: "24px", overflowX: "auto" }}>
        {(
          [
            { id: "documents", label: "Documents", icon: "📄", count: documents?.length || 0 },
            { id: "hearings", label: "Hearings", icon: "🏛️", count: hearings?.length || 0 },
            { id: "dates", label: "Dates", icon: "⏱️", count: deadlines?.length || 0 },
            { id: "tasks", label: "Tasks", icon: "📋", count: (tasks || []).filter((t) => t.status === "OPEN").length },
            { id: "client_updates", label: "Client Updates", icon: "💬", count: clientUpdates?.length || 0 },
            { id: "orders", label: "Court Orders", icon: "📜", count: orders?.length || 0 },
            { id: "timeline", label: "Timeline", icon: "⏳", count: timeline?.length || 0 },
          ] as const
        ).map((t) => {
          const active = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 16px",
                borderBottom: active ? "2px solid var(--accent)" : "2px solid transparent",
                color: active ? "var(--text-primary)" : "var(--text-secondary)",
                fontWeight: active ? "600" : "500",
                fontSize: "14px",
                background: "none",
                borderTop: "none",
                borderLeft: "none",
                borderRight: "none",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
              <span
                style={{
                  fontSize: "11px",
                  padding: "1px 6px",
                  borderRadius: "10px",
                  backgroundColor: active ? "var(--accent)" : "rgba(255, 255, 255, 0.08)",
                  color: active ? "#ffffff" : "var(--text-muted)",
                }}
              >
                {t.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Document Vault Section */}
      {activeTab === "documents" && (
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
      )}

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

      {/* Hearings Section */}
      {activeTab === "hearings" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Hearings & Court Listings</h2>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "2px 0 0" }}>
                Scheduled listings and tribunal appearance records
              </p>
            </div>
            <button
              onClick={() => setShowHearingForm(!showHearingForm)}
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
              {showHearingForm ? "Cancel" : "+ Add Hearing"}
            </button>
          </div>

          {showHearingForm && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (hearingDate) {
                  createHearingMutation.mutate({
                    date: hearingDate,
                    court_no: hearingCourtNo || undefined,
                    item_no: hearingItemNo || undefined,
                    bench: hearingBench || undefined,
                    purpose: hearingPurpose || undefined,
                  });
                }
              }}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                padding: "20px",
                marginBottom: "20px",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "12px",
              }}
            >
              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Hearing Date *
                </label>
                <input
                  type="date"
                  required
                  value={hearingDate}
                  onChange={(e) => setHearingDate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Court No.
                </label>
                <input
                  type="text"
                  placeholder="e.g. 1"
                  value={hearingCourtNo}
                  onChange={(e) => setHearingCourtNo(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Item No.
                </label>
                <input
                  type="text"
                  placeholder="e.g. 24"
                  value={hearingItemNo}
                  onChange={(e) => setHearingItemNo(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Bench / Court
                </label>
                <input
                  type="text"
                  placeholder={matter.court_or_forum || "e.g. NCLT Mumbai"}
                  value={hearingBench}
                  onChange={(e) => setHearingBench(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div style={{ gridColumn: "1 / -1" }}>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Purpose
                </label>
                <input
                  type="text"
                  placeholder="e.g. First listing for admission / Arguments on IA"
                  value={hearingPurpose}
                  onChange={(e) => setHearingPurpose(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowHearingForm(false)}
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
                  disabled={createHearingMutation.isPending}
                  style={{
                    padding: "8px 18px",
                    borderRadius: "6px",
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    border: "none",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {createHearingMutation.isPending ? "Saving..." : "Save Hearing"}
                </button>
              </div>
            </form>
          )}

          {hearingsLoading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>Loading hearings...</div>
          ) : !hearings || hearings.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                backgroundColor: "var(--bg-secondary)",
                border: "2px dashed var(--border)",
                borderRadius: "12px",
              }}
            >
              <p style={{ fontSize: "16px", fontWeight: "600", marginBottom: "6px" }}>No Hearings Scheduled</p>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "16px" }}>
                Manually record court listings or let automatic NCLT cause list matching find them.
              </p>
              <button
                onClick={() => setShowHearingForm(true)}
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
                + Add First Hearing
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {hearings.map((h) => (
                <div
                  key={h.hearing_id}
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: "10px",
                    padding: "18px 20px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: "12px",
                  }}
                >
                  <div style={{ flex: 1, minWidth: "260px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "6px" }}>
                      <span style={{ fontSize: "15px", fontWeight: "700" }}>{h.date}</span>
                      {h.court_no && (
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "11px",
                            fontWeight: "700",
                            backgroundColor: "rgba(59, 130, 246, 0.15)",
                            color: "var(--accent)",
                          }}
                        >
                          Court {h.court_no}
                        </span>
                      )}
                      {h.item_no && (
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "11px",
                            fontWeight: "600",
                            backgroundColor: "rgba(255, 255, 255, 0.08)",
                          }}
                        >
                          Item #{h.item_no}
                        </span>
                      )}
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "11px",
                          fontWeight: "600",
                          backgroundColor: h.source === "CAUSE_LIST" ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.05)",
                          color: h.source === "CAUSE_LIST" ? "var(--success)" : "var(--text-muted)",
                        }}
                      >
                        {h.source === "CAUSE_LIST" ? "NCLT Cause List" : "Manual"}
                      </span>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "11px",
                          fontWeight: "600",
                          backgroundColor: h.status === "HEARD" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                          color: h.status === "HEARD" ? "var(--success)" : "#f59e0b",
                        }}
                      >
                        {h.status}
                      </span>
                    </div>

                    <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                      {h.court_or_forum || h.bench || matter.court_or_forum}
                      {h.purpose && ` • Purpose: ${h.purpose}`}
                    </div>

                    {h.outcome && (
                      <div
                        style={{
                          marginTop: "8px",
                          padding: "8px 12px",
                          backgroundColor: "rgba(255, 255, 255, 0.03)",
                          borderRadius: "6px",
                          borderLeft: "3px solid var(--accent)",
                          fontSize: "13px",
                        }}
                      >
                        <strong>Outcome:</strong> {h.outcome}
                      </div>
                    )}

                    {(h as any).source_note && (
                      <div
                        style={{
                          marginTop: "6px",
                          fontSize: "12px",
                          color: "var(--text-muted)",
                          fontStyle: "italic",
                        }}
                      >
                        {(h as any).source_note}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => {
                      setOutcomeHearing(h);
                      setOutcomeStatus(h.status === "LISTED" ? "HEARD" : h.status);
                      setOutcomeText(h.outcome || "");
                      setNextHearingDate("");
                      setNextHearingPurpose("");
                    }}
                    style={{
                      padding: "8px 14px",
                      borderRadius: "6px",
                      backgroundColor: "var(--bg-primary)",
                      border: "1px solid var(--border)",
                      color: "var(--text-primary)",
                      fontSize: "13px",
                      fontWeight: "600",
                      cursor: "pointer",
                      minHeight: "44px",
                    }}
                  >
                    📝 Record Outcome
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Dates Section */}
      {activeTab === "dates" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Dates & Procedural Clock</h2>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "2px 0 0" }}>
                Filing deadlines, limitation dates, and internal targets
              </p>
            </div>
            <button
              onClick={() => setShowDeadlineForm(!showDeadlineForm)}
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
              {showDeadlineForm ? "Cancel" : "+ Add Deadline"}
            </button>
          </div>

          {showDeadlineForm && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (deadlineLabel && deadlineDueOn) {
                  createDeadlineMutation.mutate({
                    label: deadlineLabel.trim(),
                    due_on: deadlineDueOn,
                    owner: deadlineOwner.trim() || undefined,
                  });
                }
              }}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                padding: "20px",
                marginBottom: "20px",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "12px",
              }}
            >
              <div style={{ gridColumn: "1 / -1" }}>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Deadline Description / Label *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. File Reply to Section 7 Application"
                  value={deadlineLabel}
                  onChange={(e) => setDeadlineLabel(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Due Date *
                </label>
                <input
                  type="date"
                  required
                  value={deadlineDueOn}
                  onChange={(e) => setDeadlineDueOn(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Responsible Lawyer / Owner
                </label>
                <input
                  type="text"
                  placeholder="e.g. Adv. Sharma"
                  value={deadlineOwner}
                  onChange={(e) => setDeadlineOwner(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                />
              </div>

              <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowDeadlineForm(false)}
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
                  disabled={createDeadlineMutation.isPending}
                  style={{
                    padding: "8px 18px",
                    borderRadius: "6px",
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    border: "none",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {createDeadlineMutation.isPending ? "Saving..." : "Save Deadline"}
                </button>
              </div>
            </form>
          )}

          {deadlinesLoading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>Loading deadlines...</div>
          ) : !deadlines || deadlines.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                backgroundColor: "var(--bg-secondary)",
                border: "2px dashed var(--border)",
                borderRadius: "12px",
              }}
            >
              <p style={{ fontSize: "16px", fontWeight: "600", marginBottom: "6px" }}>No Deadlines Set</p>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "16px" }}>
                Add procedural deadlines or court-directed dates to track them here and on Today.
              </p>
              <button
                onClick={() => setShowDeadlineForm(true)}
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
                + Add First Deadline
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {deadlines.map((d) => (
                <div
                  key={d.deadline_id}
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
                  <div style={{ flex: 1, minWidth: "260px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{ fontSize: "14px", fontWeight: "700", color: "var(--accent)" }}>
                        Due: {d.due_on}
                      </span>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "11px",
                          fontWeight: "600",
                          backgroundColor: d.lifecycle === "DONE" ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.08)",
                          color: d.lifecycle === "DONE" ? "var(--success)" : "var(--text-secondary)",
                        }}
                      >
                        {d.lifecycle}
                      </span>
                    </div>

                    <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-primary)" }}>
                      {d.label}
                    </div>

                    <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px", fontStyle: "italic" }}>
                      {d.source_note}
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    {d.lifecycle !== "DONE" && (
                      <button
                        onClick={() => updateDeadlineMutation.mutate({ deadlineId: d.deadline_id, lifecycle: "DONE" })}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "6px",
                          backgroundColor: "rgba(16, 185, 129, 0.12)",
                          color: "var(--success)",
                          border: "1px solid rgba(16, 185, 129, 0.3)",
                          fontSize: "12px",
                          fontWeight: "600",
                          cursor: "pointer",
                        }}
                      >
                        ✓ Mark Done
                      </button>
                    )}
                    {d.lifecycle === "DONE" && (
                      <button
                        onClick={() => updateDeadlineMutation.mutate({ deadlineId: d.deadline_id, lifecycle: "CONFIRMED" })}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "6px",
                          backgroundColor: "transparent",
                          color: "var(--text-muted)",
                          border: "1px solid var(--border)",
                          fontSize: "12px",
                          cursor: "pointer",
                        }}
                      >
                        Re-open
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Orders Section */}
      {activeTab === "orders" && (
        <div>
          <div style={{ marginBottom: "16px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Court Orders (Public Mirror)</h2>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "2px 0 0" }}>
              Public tribunal orders automatically landed in this matter via IBBI public crawling
            </p>
          </div>

          {ordersLoading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>Loading orders...</div>
          ) : !orders || orders.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                backgroundColor: "var(--bg-secondary)",
                border: "2px dashed var(--border)",
                borderRadius: "12px",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No orders matched yet. When an official order matching this matter's case number is published, it will automatically appear here.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {orders.map((o) => (
                <div
                  key={o.public_id}
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: "10px",
                    padding: "18px 20px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "12px",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                      <span
                        style={{
                          backgroundColor: "rgba(245, 158, 11, 0.15)",
                          color: "#f59e0b",
                          border: "1px solid rgba(245, 158, 11, 0.3)",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "11px",
                          fontWeight: "700",
                        }}
                      >
                        Uncertified copy from official public mirror
                      </span>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                        {o.decision_date || "Date unspecified"}
                      </span>
                    </div>

                    <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-primary)" }}>
                      {o.public_id} ({o.match_key})
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                      Source: {o.source_ref}
                    </div>
                  </div>

                  <button
                    onClick={() => setViewingPublicOrder(o)}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "6px",
                      backgroundColor: "var(--accent)",
                      color: "#fff",
                      border: "none",
                      fontSize: "13px",
                      fontWeight: "600",
                      cursor: "pointer",
                      minHeight: "44px",
                    }}
                  >
                    🔍 View in Source Viewer
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Timeline Section */}
      {activeTab === "timeline" && (
        <div>
          <div style={{ marginBottom: "20px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Matter Timeline</h2>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "2px 0 0" }}>
              Unified chronological timeline of filings, hearings, deadlines, and orders
            </p>
          </div>

          {timelineLoading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>Loading timeline...</div>
          ) : !timeline || timeline.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                backgroundColor: "var(--bg-secondary)",
                border: "2px dashed var(--border)",
                borderRadius: "12px",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No timeline events recorded yet.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", borderLeft: "2px solid var(--border)", paddingLeft: "20px", marginLeft: "12px" }}>
              {timeline.map((item) => {
                const icon =
                  item.item_type === "HEARING"
                    ? "🏛️"
                    : item.item_type === "DEADLINE"
                    ? "⏱️"
                    : item.item_type === "ORDER"
                    ? "📜"
                    : "📄";
                return (
                  <div
                    key={item.id}
                    style={{
                      position: "relative",
                      backgroundColor: "var(--bg-secondary)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                      padding: "14px 18px",
                    }}
                  >
                    <span
                      style={{
                        position: "absolute",
                        left: "-31px",
                        top: "14px",
                        width: "20px",
                        height: "20px",
                        borderRadius: "50%",
                        backgroundColor: "var(--bg-primary)",
                        border: "2px solid var(--accent)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "10px",
                      }}
                    >
                      {icon}
                    </span>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--accent)" }}>
                        {item.date} • {item.item_type}
                      </span>
                      {item.status && (
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500" }}>
                          {item.status}
                        </span>
                      )}
                    </div>

                    <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)" }}>
                      {item.title}
                    </div>

                    {item.subtitle && (
                      <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                        {item.subtitle}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tasks Section */}
      {activeTab === "tasks" && (
        <TasksTab matterId={matterId} hearings={hearings || []} deadlines={deadlines || []} />
      )}

      {/* Client Updates Section */}
      {activeTab === "client_updates" && (
        <ClientUpdatesTab matterId={matterId} matterTitle={matter.title} />
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

      {/* Public Court Order Source Viewer */}
      {viewingPublicOrder && (
        <SourceViewer
          anchorId={viewingPublicOrder.public_id}
          workId={viewingPublicOrder.public_id}
          onClose={() => setViewingPublicOrder(null)}
        />
      )}

      {/* Share Link Modal */}
      {showShareLinkModal && (
        <ShareLinkModal
          matterId={matterId}
          matterTitle={matter.title}
          onClose={() => setShowShareLinkModal(false)}
        />
      )}

      {/* Record Outcome & Next Date Modal */}
      {outcomeHearing && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              padding: "24px",
              width: "100%",
              maxWidth: "520px",
              boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ fontSize: "17px", fontWeight: "700", margin: 0 }}>
                Record Hearing Outcome
              </h3>
              <button
                onClick={() => setOutcomeHearing(null)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: "18px",
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "16px" }}>
              Hearing on <strong>{outcomeHearing.date}</strong> • {outcomeHearing.court_or_forum || outcomeHearing.bench || "Court"}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                recordOutcomeMutation.mutate({
                  hearingId: outcomeHearing.hearing_id,
                  outcome: outcomeText,
                  status: outcomeStatus,
                  next_date: nextHearingDate || undefined,
                  next_purpose: nextHearingPurpose || undefined,
                });
              }}
              style={{ display: "flex", flexDirection: "column", gap: "14px" }}
            >
              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Hearing Status
                </label>
                <select
                  value={outcomeStatus}
                  onChange={(e) => setOutcomeStatus(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                >
                  <option value="HEARD">Heard</option>
                  <option value="ADJOURNED">Adjourned</option>
                  <option value="RESERVED">Order Reserved</option>
                  <option value="DISPOSED">Disposed / Final Order</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Outcome Note / Daily Order Summary *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Arguments heard in part. Time granted to Respondent to file rejoinder affidavit within 2 weeks."
                  value={outcomeText}
                  onChange={(e) => setOutcomeText(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                    resize: "vertical",
                  }}
                />
              </div>

              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
                <div style={{ fontSize: "13px", fontWeight: "700", marginBottom: "8px", color: "var(--accent)" }}>
                  Schedule Next Date (Optional)
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                      Next Date
                    </label>
                    <input
                      type="date"
                      value={nextHearingDate}
                      onChange={(e) => setNextHearingDate(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 10px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        backgroundColor: "var(--bg-primary)",
                        color: "var(--text-primary)",
                        fontSize: "13px",
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                      Next Purpose
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Further Arguments"
                      value={nextHearingPurpose}
                      onChange={(e) => setNextHearingPurpose(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 10px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        backgroundColor: "var(--bg-primary)",
                        color: "var(--text-primary)",
                        fontSize: "13px",
                      }}
                    />
                  </div>
                </div>

                {/* Optional preparation task for next date */}
                {nextHearingDate && (
                  <div
                    style={{
                      marginTop: "12px",
                      padding: "12px",
                      backgroundColor: "rgba(59, 130, 246, 0.08)",
                      border: "1px solid rgba(59, 130, 246, 0.25)",
                      borderRadius: "6px",
                    }}
                  >
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        cursor: "pointer",
                        fontSize: "13px",
                        fontWeight: "600",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={createTaskForNextDate}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setCreateTaskForNextDate(checked);
                          if (checked) {
                            setNextDateTaskTitle(`Prepare for listing on ${nextHearingDate}`);
                            setNextDateTaskDueOn(getPreviousWorkingDay(nextHearingDate));
                            if (assignableMembers.length > 0 && !nextDateTaskAssignee) {
                              setNextDateTaskAssignee(assignableMembers[0].user_id);
                            }
                          }
                        }}
                      />
                      <span>📋 Add preparation task for next date</span>
                    </label>

                    {createTaskForNextDate && (
                      <div style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "8px" }}>
                        <div>
                          <label style={{ fontSize: "11px", fontWeight: "600", display: "block", marginBottom: "2px" }}>
                            Task Title
                          </label>
                          <input
                            type="text"
                            value={nextDateTaskTitle}
                            onChange={(e) => setNextDateTaskTitle(e.target.value)}
                            style={{
                              width: "100%",
                              padding: "6px 8px",
                              borderRadius: "4px",
                              border: "1px solid var(--border)",
                              backgroundColor: "var(--bg-primary)",
                              color: "var(--text-primary)",
                              fontSize: "12px",
                            }}
                          />
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                          <div>
                            <label style={{ fontSize: "11px", fontWeight: "600", display: "block", marginBottom: "2px" }}>
                              Due Date (Prev Working Day)
                            </label>
                            <input
                              type="date"
                              value={nextDateTaskDueOn}
                              onChange={(e) => setNextDateTaskDueOn(e.target.value)}
                              style={{
                                width: "100%",
                                padding: "6px 8px",
                                borderRadius: "4px",
                                border: "1px solid var(--border)",
                                backgroundColor: "var(--bg-primary)",
                                color: "var(--text-primary)",
                                fontSize: "12px",
                              }}
                            />
                          </div>
                          <div>
                            <label style={{ fontSize: "11px", fontWeight: "600", display: "block", marginBottom: "2px" }}>
                              Assignee *
                            </label>
                            <select
                              value={nextDateTaskAssignee}
                              onChange={(e) => setNextDateTaskAssignee(e.target.value)}
                              style={{
                                width: "100%",
                                padding: "6px 8px",
                                borderRadius: "4px",
                                border: "1px solid var(--border)",
                                backgroundColor: "var(--bg-primary)",
                                color: "var(--text-primary)",
                                fontSize: "12px",
                              }}
                            >
                              <option value="">Select Assignee</option>
                              {assignableMembers.map((m) => (
                                <option key={m.user_id} value={m.user_id}>
                                  {m.display_name} ({m.role})
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
                <button
                  type="button"
                  onClick={() => setOutcomeHearing(null)}
                  style={{
                    padding: "8px 16px",
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
                  disabled={recordOutcomeMutation.isPending}
                  style={{
                    padding: "8px 20px",
                    borderRadius: "6px",
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    border: "none",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {recordOutcomeMutation.isPending ? "Saving..." : "Save Outcome"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
