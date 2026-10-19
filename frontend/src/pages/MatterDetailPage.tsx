import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMatter,
  fetchMatterDocuments,
  addCaseLink,
  removeCaseLink,
  uploadDocument,
  getDocumentDownloadUrl,
  fetchMatterHearings,
  createMatterHearing,
  recordHearingOutcome,
  fetchMatterDeadlines,
  getMatterCalendarExportUrl,
  type PdocResponse,
  type HearingResponse,
} from "../api/client";
import { SourceViewer } from "../components/SourceViewer";
import { TasksTab } from "../components/TasksTab";
import { ClientUpdatesTab } from "../components/ClientUpdatesTab";
import {
  PageHeader,
  Button,
  Input,
  Select,
  Tabs,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Modal,
  EmptyState,
} from "../components/ui";
import { formatDate, formatStatus } from "../utils/format";

interface MatterDetailPageProps {
  matterId: string;
  onBack: () => void;
  onSelectClient?: (clientId: string) => void;
}

export type MatterDetailTab =
  | "overview"
  | "hearings"
  | "tasks"
  | "documents"
  | "client_updates";

export const MatterDetailPage: React.FC<MatterDetailPageProps> = ({
  matterId,
  onBack,
  onSelectClient,
}) => {
  const queryClient = useQueryClient();

  // Tab state: Overview, Hearings, Tasks, Documents, Client updates
  const [activeTab, setActiveTab] = useState<MatterDetailTab>("overview");

  // Modals
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showHearingModal, setShowHearingModal] = useState(false);
  const [showCaseLinkModal, setShowCaseLinkModal] = useState(false);
  const [outcomeHearing, setOutcomeHearing] = useState<HearingResponse | null>(null);

  // Source viewer
  const [viewingPdoc, setViewingPdoc] = useState<{ pdocId: string; pver: string } | null>(null);

  // Case link form
  const [caseScheme, setCaseScheme] = useState("CASE_NO");
  const [caseValue, setCaseValue] = useState("");

  // Upload form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [stage, setStage] = useState("ORDER");
  const [provenanceChoice, setProvenanceChoice] = useState<"COURT" | "CLIENT" | "FIRM" | "OPPONENT" | "THIRD_PARTY">("COURT");
  const [docType, setDocType] = useState("ORDER");
  const [docTitle, setDocTitle] = useState("");
  const [versionTargetPdocId, setVersionTargetPdocId] = useState<string | null>(null);

  // Hearing form state
  const [hearingDate, setHearingDate] = useState("");
  const [hearingCourtNo, setHearingCourtNo] = useState("");
  const [hearingItemNo, setHearingItemNo] = useState("");
  const [hearingBench, setHearingBench] = useState("");
  const [hearingPurpose, setHearingPurpose] = useState("");

  // Outcome modal state
  const [outcomeStatus, setOutcomeStatus] = useState<string>("HEARD");
  const [outcomeNotes, setOutcomeNotes] = useState("");
  const [nextHearingDate, setNextHearingDate] = useState("");
  const [nextHearingPurpose, setNextHearingPurpose] = useState("");

  const [actionError, setActionError] = useState<string | null>(null);

  // Queries
  const { data, isLoading, error } = useQuery({
    queryKey: ["matter", matterId],
    queryFn: () => fetchMatter(matterId),
  });

  const { data: documents = [] } = useQuery<PdocResponse[]>({
    queryKey: ["matter_documents", matterId],
    queryFn: () => fetchMatterDocuments(matterId),
  });

  const { data: hearings = [] } = useQuery<HearingResponse[]>({
    queryKey: ["matter_hearings", matterId],
    queryFn: () => fetchMatterHearings(matterId),
  });

  const { data: deadlines = [] } = useQuery({
    queryKey: ["matter_deadlines", matterId],
    queryFn: () => fetchMatterDeadlines(matterId),
  });

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) throw new Error("No file selected");
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("stage", stage);
      formData.append("provenance", provenanceChoice);
      formData.append("doc_type", docType);
      if (docTitle.trim()) formData.append("title", docTitle.trim());
      if (versionTargetPdocId) formData.append("pdoc_id", versionTargetPdocId);
      return uploadDocument(matterId, formData);
    },
    onSuccess: () => {
      setShowUploadModal(false);
      setSelectedFile(null);
      setDocTitle("");
      setVersionTargetPdocId(null);
      queryClient.invalidateQueries({ queryKey: ["matter_documents", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to upload document.");
    },
  });

  const addHearingMutation = useMutation({
    mutationFn: () =>
      createMatterHearing(matterId, {
        date: hearingDate,
        court_no: hearingCourtNo.trim() || undefined,
        item_no: hearingItemNo.trim() || undefined,
        bench: hearingBench.trim() || undefined,
        purpose: hearingPurpose.trim() || undefined,
      }),
    onSuccess: () => {
      setShowHearingModal(false);
      setHearingDate("");
      setHearingCourtNo("");
      setHearingItemNo("");
      setHearingBench("");
      setHearingPurpose("");
      queryClient.invalidateQueries({ queryKey: ["matter_hearings", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to add hearing.");
    },
  });

  const recordOutcomeMutation = useMutation({
    mutationFn: () => {
      if (!outcomeHearing) throw new Error("No hearing selected");
      return recordHearingOutcome(outcomeHearing.hearing_id, {
        outcome: outcomeNotes.trim() || outcomeStatus,
        status: outcomeStatus,
        next_date: nextHearingDate || undefined,
        next_purpose: nextHearingPurpose.trim() || undefined,
      });
    },
    onSuccess: () => {
      setOutcomeHearing(null);
      setOutcomeStatus("HEARD");
      setOutcomeNotes("");
      setNextHearingDate("");
      setNextHearingPurpose("");
      queryClient.invalidateQueries({ queryKey: ["matter_hearings", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to record outcome.");
    },
  });

  const addLinkMutation = useMutation({
    mutationFn: () =>
      addCaseLink(matterId, {
        scheme: caseScheme,
        value_normalized: caseValue.trim(),
        role: "CASE",
        track: true,
      }),
    onSuccess: () => {
      setShowCaseLinkModal(false);
      setCaseValue("");
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to link case identifier.");
    },
  });

  const removeLinkMutation = useMutation({
    mutationFn: ({ scheme, valueNormalized }: { scheme: string; valueNormalized: string }) =>
      removeCaseLink(matterId, scheme, valueNormalized),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter", matterId] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to remove case link.");
    },
  });

  if (isLoading) {
    return <p style={{ color: "var(--text-muted)" }}>Loading matter file...</p>;
  }

  if (error || !data) {
    return (
      <p style={{ color: "var(--status-overdue-text)" }}>
        Failed to load matter: {error instanceof Error ? error.message : String(error)}
      </p>
    );
  }

  const matterItem = data.matter;
  const clientItem = data.client;
  const caseLinks = data.case_links || [];

  // Short header components: client, case number, court, next date
  const clientName = clientItem?.display_name || "Client";
  const caseNumber = caseLinks.find((l) => l.scheme === "CASE_NO")?.value_normalized || caseLinks[0]?.value_normalized || "No case number";
  const courtName = matterItem.court_or_forum || "Court";
  const nextListedHearing = hearings.find((h) => h.status === "LISTED");
  const nextDateStr = nextListedHearing?.date ? formatDate(nextListedHearing.date) : "No date set";

  const headerDescription = (
    <span>
      {onSelectClient && matterItem.client_id ? (
        <button
          type="button"
          onClick={() => onSelectClient(matterItem.client_id!)}
          style={{ color: "var(--accent-link)", cursor: "pointer", fontSize: "inherit" }}
        >
          {clientName}
        </button>
      ) : (
        clientName
      )}
      {" • "}
      {caseNumber}
      {" • "}
      {courtName}
      {" • "}
      <span>Next date: {nextDateStr}</span>
    </span>
  );

  // One primary action depending on active tab
  let primaryAction: { label: string; onClick: () => void } | undefined;
  if (activeTab === "hearings") {
    primaryAction = {
      label: "Add hearing",
      onClick: () => {
        setActionError(null);
        setShowHearingModal(true);
      },
    };
  } else if (activeTab === "documents") {
    primaryAction = {
      label: "Upload document",
      onClick: () => {
        setActionError(null);
        setSelectedFile(null);
        setDocTitle("");
        setVersionTargetPdocId(null);
        setShowUploadModal(true);
      },
    };
  } else if (activeTab === "overview") {
    primaryAction = {
      label: "Add case link",
      onClick: () => {
        setActionError(null);
        setShowCaseLinkModal(true);
      },
    };
  }

  const moreActions = [
    {
      label: "Export calendar (.ics)",
      onClick: () => {
        window.open(getMatterCalendarExportUrl(matterId), "_blank");
      },
    },
    {
      label: "Add case link",
      onClick: () => {
        setActionError(null);
        setShowCaseLinkModal(true);
      },
    },
  ];

  const tabs = [
    { id: "overview" as const, label: "Overview" },
    { id: "hearings" as const, label: "Hearings", count: hearings.length },
    { id: "tasks" as const, label: "Tasks" },
    { id: "documents" as const, label: "Documents", count: documents.length },
    { id: "client_updates" as const, label: "Client updates" },
  ];

  return (
    <div>
      <PageHeader
        title={matterItem.title}
        description={headerDescription}
        onBack={onBack}
        primaryAction={primaryAction}
        moreActions={moreActions}
      />

      {actionError && (
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
          {actionError}
        </div>
      )}

      {/* Tabs navigation */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id)}
      />

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          <section>
            <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, marginBottom: "var(--space-3)" }}>
              Matter details
            </h2>
            <Table>
              <Tbody>
                <Tr>
                  <Td style={{ width: "200px", color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Client</Td>
                  <Td style={{ fontWeight: 500 }}>{clientName}</Td>
                </Tr>
                <Tr>
                  <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Case type</Td>
                  <Td>{matterItem.case_type || "—"}</Td>
                </Tr>
                <Tr>
                  <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Court or forum</Td>
                  <Td>{matterItem.court_or_forum || "—"}</Td>
                </Tr>
                <Tr>
                  <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Client role</Td>
                  <Td>{formatStatus(matterItem.client_role)}</Td>
                </Tr>
                <Tr>
                  <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Status</Td>
                  <Td>
                    <Badge variant={matterItem.status === "CLOSED" ? "neutral" : "done"}>
                      {formatStatus(matterItem.status)}
                    </Badge>
                  </Td>
                </Tr>
                <Tr>
                  <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Next hearing</Td>
                  <Td>{nextDateStr}</Td>
                </Tr>
              </Tbody>
            </Table>
          </section>

          {/* Linked Identifiers */}
          <section>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
              <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600 }}>
                Case identifiers ({caseLinks.length})
              </h2>
            </div>

            {caseLinks.length === 0 ? (
              <EmptyState
                message="No official court case numbers linked yet."
                action={
                  <Button variant="secondary" size="sm" onClick={() => setShowCaseLinkModal(true)}>
                    Add case link
                  </Button>
                }
              />
            ) : (
              <Table>
                <Thead>
                  <Tr>
                    <Th>Scheme</Th>
                    <Th>Identifier value</Th>
                    <Th style={{ width: "80px" }}></Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {caseLinks.map((link) => (
                    <Tr key={`${link.scheme}-${link.value_normalized}`}>
                      <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
                        {formatStatus(link.scheme)}
                      </Td>
                      <Td style={{ fontWeight: 500 }}>{link.value_normalized}</Td>
                      <Td>
                        <Button
                          variant="quiet"
                          size="sm"
                          onClick={() =>
                            removeLinkMutation.mutate({
                              scheme: link.scheme,
                              valueNormalized: link.value_normalized,
                            })
                          }
                          style={{ color: "var(--status-overdue-text)" }}
                        >
                          Remove
                        </Button>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </section>
        </div>
      )}

      {/* Tab 2: Hearings */}
      {activeTab === "hearings" && (
        <div>
          {hearings.length === 0 ? (
            <EmptyState
              message="No hearings scheduled for this matter."
              action={
                <Button variant="secondary" size="sm" onClick={() => setShowHearingModal(true)}>
                  Add hearing
                </Button>
              }
            />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>Date</Th>
                  <Th>Court</Th>
                  <Th>Item</Th>
                  <Th>Bench</Th>
                  <Th>Purpose</Th>
                  <Th>Status / Outcome</Th>
                  <Th style={{ width: "120px" }}></Th>
                </Tr>
              </Thead>
              <Tbody>
                {hearings.map((h) => {
                  const isListed = h.status === "LISTED";
                  return (
                    <Tr key={h.hearing_id}>
                      <Td style={{ fontWeight: 500 }}>{formatDate(h.date)}</Td>
                      <Td style={{ color: "var(--text-muted)" }}>
                        {h.court_or_forum || (h.court_no ? (h.court_no.trim().toLowerCase().startsWith("court") ? h.court_no.trim() : `Court ${h.court_no.trim()}`) : "—")}
                      </Td>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                        {h.item_no ? `Item ${h.item_no}` : "—"}
                      </Td>
                      <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                        {h.bench || "—"}
                      </Td>
                      <Td style={{ fontSize: "var(--text-sm)" }}>
                        {h.purpose ? formatStatus(h.purpose) : "—"}
                      </Td>
                      <Td>
                        <Badge variant={isListed ? "neutral" : "done"}>
                          {formatStatus(h.status)}
                        </Badge>
                      </Td>
                      <Td>
                        {isListed && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setActionError(null);
                              setOutcomeHearing(h);
                            }}
                          >
                            Outcome
                          </Button>
                        )}
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          )}
        </div>
      )}

      {/* Tab 3: Tasks */}
      {activeTab === "tasks" && (
        <TasksTab matterId={matterId} hearings={hearings} deadlines={deadlines} />
      )}

      {/* Tab 4: Documents */}
      {activeTab === "documents" && (
        <div>
          {documents.length === 0 ? (
            <EmptyState
              message="No documents in vault for this matter."
              action={
                <Button variant="secondary" size="sm" onClick={() => setShowUploadModal(true)}>
                  Upload document
                </Button>
              }
            />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>Document title</Th>
                  <Th>Stage</Th>
                  <Th>Type</Th>
                  <Th>Provenance</Th>
                  <Th>Uploaded</Th>
                  <Th style={{ width: "140px" }}></Th>
                </Tr>
              </Thead>
              <Tbody>
                {documents.map((doc) => (
                  <Tr key={doc.pdoc_id}>
                    <Td style={{ fontWeight: 500 }}>{doc.title || "Document"}</Td>
                    <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
                      {formatStatus(doc.stage)}
                    </Td>
                    <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
                      {formatStatus(doc.doc_type)}
                    </Td>
                    <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
                      {formatStatus(doc.provenance)}
                    </Td>
                    <Td style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
                      {formatDate(doc.created_at)}
                    </Td>
                    <Td>
                      <div style={{ display: "flex", gap: "var(--space-1)" }}>
                        <a
                          href={getDocumentDownloadUrl(matterId, doc.pdoc_id)}
                          download
                          style={{
                            fontSize: "var(--text-sm)",
                            padding: "4px 8px",
                            borderRadius: "var(--radius-sm)",
                            border: "1px solid var(--border-main)",
                            color: "var(--text-main)",
                            textDecoration: "none",
                          }}
                        >
                          Download
                        </a>
                        <Button
                          variant="quiet"
                          size="sm"
                          onClick={() => setViewingPdoc({ pdocId: doc.pdoc_id, pver: doc.current_version || "v1" })}
                        >
                          View
                        </Button>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </div>
      )}

      {/* Tab 5: Client updates */}
      {activeTab === "client_updates" && (
        <ClientUpdatesTab matterId={matterId} matterTitle={matterItem.title} />
      )}

      {/* Add Hearing Modal */}
      <Modal
        isOpen={showHearingModal}
        onClose={() => setShowHearingModal(false)}
        title="Add hearing"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowHearingModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => addHearingMutation.mutate()}
              disabled={addHearingMutation.isPending || !hearingDate}
            >
              {addHearingMutation.isPending ? "Adding..." : "Add hearing"}
            </Button>
          </>
        }
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            addHearingMutation.mutate();
          }}
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}
        >
          <Input
            label="Hearing date *"
            type="date"
            value={hearingDate}
            onChange={(e) => setHearingDate(e.target.value)}
            required
            autoFocus
          />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Input
              label="Court or forum number"
              value={hearingCourtNo}
              onChange={(e) => setHearingCourtNo(e.target.value)}
              placeholder="e.g. Court Room 1"
            />
            <Input
              label="Cause list item number"
              value={hearingItemNo}
              onChange={(e) => setHearingItemNo(e.target.value)}
              placeholder="e.g. 14"
            />
          </div>

          <Input
            label="Bench / Judge"
            value={hearingBench}
            onChange={(e) => setHearingBench(e.target.value)}
            placeholder="e.g. Chief Justice Bench"
          />

          <Input
            label="Purpose of listing"
            value={hearingPurpose}
            onChange={(e) => setHearingPurpose(e.target.value)}
            placeholder="e.g. Admission, Final hearing"
          />
        </form>
      </Modal>

      {/* Record Outcome Modal */}
      {outcomeHearing && (
        <Modal
          isOpen
          onClose={() => setOutcomeHearing(null)}
          title={`Record outcome • ${formatDate(outcomeHearing.date)}`}
          footer={
            <>
              <Button variant="secondary" onClick={() => setOutcomeHearing(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => recordOutcomeMutation.mutate()}
                disabled={recordOutcomeMutation.isPending}
              >
                {recordOutcomeMutation.isPending ? "Recording..." : "Save outcome"}
              </Button>
            </>
          }
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            <Select
              label="Hearing status *"
              value={outcomeStatus}
              onChange={(e) => setOutcomeStatus(e.target.value)}
              options={[
                { value: "HEARD", label: "Heard" },
                { value: "ADJOURNED", label: "Adjourned" },
                { value: "NOT_REACHED", label: "Not reached" },
                { value: "PASS_OVER", label: "Passed over" },
                { value: "DISPOSED", label: "Disposed" },
              ]}
            />

            <div className="form-group">
              <label className="form-label">Outcome summary notes</label>
              <textarea
                className="textarea"
                rows={3}
                value={outcomeNotes}
                onChange={(e) => setOutcomeNotes(e.target.value)}
                placeholder="What transpired before the bench..."
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
              <Input
                label="Next hearing date"
                type="date"
                value={nextHearingDate}
                onChange={(e) => setNextHearingDate(e.target.value)}
              />
              <Input
                label="Next listing purpose"
                value={nextHearingPurpose}
                onChange={(e) => setNextHearingPurpose(e.target.value)}
                placeholder="e.g. Compliance"
              />
            </div>
          </div>
        </Modal>
      )}

      {/* Add Case Link Modal */}
      <Modal
        isOpen={showCaseLinkModal}
        onClose={() => setShowCaseLinkModal(false)}
        title="Add case identifier"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCaseLinkModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => addLinkMutation.mutate()}
              disabled={addLinkMutation.isPending || !caseValue.trim()}
            >
              {addLinkMutation.isPending ? "Linking..." : "Link identifier"}
            </Button>
          </>
        }
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          <Select
            label="Scheme"
            value={caseScheme}
            onChange={(e) => setCaseScheme(e.target.value)}
            options={[
              { value: "CASE_NO", label: "Case number (e.g. CP(IB)/123/MB/2026)" },
              { value: "CNR", label: "CNR (e.g. NCLT010012342026)" },
              { value: "DIARY_NO", label: "Diary number" },
            ]}
          />

          <Input
            label="Identifier value *"
            value={caseValue}
            onChange={(e) => setCaseValue(e.target.value)}
            placeholder="e.g. CP (IB) No. 456/KB/2026"
            required
            autoFocus
          />
        </div>
      </Modal>

      {/* Upload Document Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Upload document"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowUploadModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => uploadMutation.mutate()}
              disabled={uploadMutation.isPending || !selectedFile}
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload document"}
            </Button>
          </>
        }
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          <div className="form-group">
            <label className="form-label">Select file (PDF, DOCX, EML, ZIP) *</label>
            <input
              type="file"
              className="input"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setSelectedFile(e.target.files[0]);
                  if (!docTitle) {
                    setDocTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ""));
                  }
                }
              }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Input
              label="Document title"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Descriptive title"
            />
            <Select
              label="Document type"
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              options={[
                { value: "ORDER", label: "Order" },
                { value: "PETITION", label: "Petition" },
                { value: "APPLICATION", label: "Application" },
                { value: "AFFIDAVIT", label: "Affidavit" },
                { value: "NOTICE", label: "Notice" },
                { value: "REPLY", label: "Reply" },
                { value: "MEMO", label: "Memo" },
                { value: "OTHER", label: "Other" },
              ]}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Select
              label="Stage"
              value={stage}
              onChange={(e) => setStage(e.target.value)}
              options={[
                { value: "ORDER", label: "Order" },
                { value: "PLEADINGS", label: "Pleadings" },
                { value: "EVIDENCE", label: "Evidence" },
                { value: "CORRESPONDENCE", label: "Correspondence" },
                { value: "MISC", label: "Miscellaneous" },
              ]}
            />
            <Select
              label="Provenance"
              value={provenanceChoice}
              onChange={(e) => setProvenanceChoice(e.target.value as typeof provenanceChoice)}
              options={[
                { value: "COURT", label: "Court" },
                { value: "CLIENT", label: "Client" },
                { value: "FIRM", label: "Firm" },
                { value: "OPPONENT", label: "Opponent" },
                { value: "THIRD_PARTY", label: "Third party" },
              ]}
            />
          </div>
        </div>
      </Modal>

      {/* Source Viewer Drawer */}
      {viewingPdoc && (
        <SourceViewer
          anchorId={`pdoc_${viewingPdoc.pdocId}/${viewingPdoc.pver}#1`}
          pdocId={viewingPdoc.pdocId}
          pver={viewingPdoc.pver}
          onClose={() => setViewingPdoc(null)}
        />
      )}
    </div>
  );
};
