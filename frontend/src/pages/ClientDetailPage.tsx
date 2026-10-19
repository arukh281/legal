import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchClient,
  archiveClient,
  createMatter,
  type MatterCreateRequest,
  type ClientDetailResponse,
} from "../api/client";
import {
  PageHeader,
  Button,
  Input,
  Select,
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

interface ClientDetailPageProps {
  clientId: string;
  onBack: () => void;
  onSelectMatter: (matterId: string) => void;
}

export const ClientDetailPage: React.FC<ClientDetailPageProps> = ({
  clientId,
  onBack,
  onSelectMatter,
}) => {
  const queryClient = useQueryClient();
  const [showMatterModal, setShowMatterModal] = useState(false);

  // Matter form
  const [title, setTitle] = useState("");
  const [caseType, setCaseType] = useState("Insolvency (IBC)");
  const [court, setCourt] = useState("NCLT Mumbai");
  const [clientRole, setClientRole] = useState("PETITIONER");
  const [clientMatterNo, setClientMatterNo] = useState("");
  const [walled, setWalled] = useState(false);

  const { data, isLoading, error } = useQuery<ClientDetailResponse>({
    queryKey: ["client", clientId],
    queryFn: () => fetchClient(clientId),
  });

  const archiveMutation = useMutation({
    mutationFn: () => archiveClient(clientId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["client", clientId] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });

  const createMatterMutation = useMutation({
    mutationFn: (req: MatterCreateRequest) => createMatter(req),
    onSuccess: (newMatter) => {
      queryClient.invalidateQueries({ queryKey: ["client", clientId] });
      queryClient.invalidateQueries({ queryKey: ["matters"] });
      setShowMatterModal(false);
      resetMatterForm();
      onSelectMatter(newMatter.matter_id);
    },
  });

  const resetMatterForm = () => {
    setTitle("");
    setCaseType("Insolvency (IBC)");
    setCourt("NCLT Mumbai");
    setClientRole("PETITIONER");
    setClientMatterNo("");
    setWalled(false);
  };

  const handleMatterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    createMatterMutation.mutate({
      client_id: clientId,
      title: title.trim(),
      case_type: caseType.trim() || undefined,
      court_or_forum: court.trim() || undefined,
      client_role: clientRole,
      client_matter_no: clientMatterNo.trim() || undefined,
      walled,
    });
  };

  if (isLoading) {
    return <p style={{ color: "var(--text-muted)" }}>Loading client details...</p>;
  }

  if (error || !data) {
    return (
      <p style={{ color: "var(--status-overdue-text)" }}>
        Failed to load client: {error instanceof Error ? error.message : String(error)}
      </p>
    );
  }

  const client = data.client;
  const matters = data.matters || [];
  const contact = (client.contact || {}) as Record<string, string>;
  const ids = (client.identifiers || {}) as Record<string, string>;
  const isArchived = client.status === "ARCHIVED";

  const descriptionParts = [
    formatStatus(client.client_type),
    ids.CIN && `CIN: ${ids.CIN}`,
    ids.PAN && `PAN: ${ids.PAN}`,
    contact.name && `Contact: ${contact.name}`,
    contact.email,
  ].filter(Boolean);

  const moreActions = [
    {
      label: isArchived ? "Unarchive client" : "Archive client",
      onClick: () => archiveMutation.mutate(),
    },
  ];

  return (
    <div>
      <PageHeader
        title={client.display_name}
        description={descriptionParts.join(" • ")}
        onBack={onBack}
        primaryAction={{
          label: "New matter",
          onClick: () => setShowMatterModal(true),
        }}
        moreActions={moreActions}
      />

      <div style={{ marginBottom: "var(--space-6)" }}>
        <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, marginBottom: "var(--space-3)" }}>
          Matters ({matters.length})
        </h2>

        {matters.length === 0 ? (
          <EmptyState
            message="No matters opened under this client yet."
            action={
              <Button variant="secondary" size="sm" onClick={() => setShowMatterModal(true)}>
                New matter
              </Button>
            }
          />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>Matter title</Th>
                <Th>Case type</Th>
                <Th>Court or forum</Th>
                <Th>Role</Th>
                <Th>Status</Th>
                <Th>Created</Th>
              </Tr>
            </Thead>
            <Tbody>
              {matters.map((m) => (
                <Tr key={m.matter_id} clickable onClick={() => onSelectMatter(m.matter_id)}>
                  <Td style={{ fontWeight: 500 }}>{m.title}</Td>
                  <Td style={{ color: "var(--text-muted)" }}>{m.case_type || "—"}</Td>
                  <Td style={{ color: "var(--text-muted)" }}>{m.court_or_forum || "—"}</Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {formatStatus(m.client_role)}
                  </Td>
                  <Td>
                    <Badge variant={m.status === "CLOSED" ? "neutral" : "done"}>
                      {formatStatus(m.status)}
                    </Badge>
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {formatDate(m.created_at)}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </div>

      {/* New Matter Modal */}
      <Modal
        isOpen={showMatterModal}
        onClose={() => setShowMatterModal(false)}
        title="New matter"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowMatterModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleMatterSubmit}
              disabled={createMatterMutation.isPending || !title.trim()}
            >
              {createMatterMutation.isPending ? "Creating..." : "Create matter"}
            </Button>
          </>
        }
      >
        <form onSubmit={handleMatterSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          {createMatterMutation.error && (
            <p style={{ color: "var(--status-overdue-text)", fontSize: "var(--text-sm)" }}>
              {createMatterMutation.error instanceof Error
                ? createMatterMutation.error.message
                : "Failed to create matter"}
            </p>
          )}

          <Input
            label="Matter title *"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Insolvency petition against ABC Corp"
            required
            autoFocus
          />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Input
              label="Case type"
              value={caseType}
              onChange={(e) => setCaseType(e.target.value)}
              placeholder="e.g. Insolvency (IBC)"
            />
            <Input
              label="Court or forum"
              value={court}
              onChange={(e) => setCourt(e.target.value)}
              placeholder="e.g. NCLT Mumbai"
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Select
              label="Client role"
              value={clientRole}
              onChange={(e) => setClientRole(e.target.value)}
              options={[
                { value: "PETITIONER", label: "Petitioner" },
                { value: "RESPONDENT", label: "Respondent" },
                { value: "APPLICANT", label: "Applicant" },
                { value: "DEFENDANT", label: "Defendant" },
                { value: "APPELLANT", label: "Appellant" },
                { value: "INTERVENOR", label: "Intervenor" },
                { value: "THIRD_PARTY", label: "Third party" },
              ]}
            />
            <Input
              label="Client matter reference"
              value={clientMatterNo}
              onChange={(e) => setClientMatterNo(e.target.value)}
              placeholder="e.g. CLI-2026-001"
            />
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "var(--text-sm)", cursor: "pointer", marginTop: "4px" }}>
            <input
              type="checkbox"
              checked={walled}
              onChange={(e) => setWalled(e.target.checked)}
              style={{ accentColor: "var(--accent-main)" }}
            />
            <span>Confidential ethical wall (restricts access to assigned team)</span>
          </label>
        </form>
      </Modal>
    </div>
  );
};
