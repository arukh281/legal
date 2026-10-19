import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAllMatters, type MatterSummaryResponse } from "../api/client";
import { MatterDetailPage } from "./MatterDetailPage";
import { ClientDetailPage } from "./ClientDetailPage";
import {
  PageHeader,
  Input,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  EmptyState,
} from "../components/ui";
import { formatDate, formatStatus } from "../utils/format";

interface MattersPageProps {
  initialMatterId?: string | null;
  onSelectClient?: (clientId: string) => void;
}

export const MattersPage: React.FC<MattersPageProps> = ({
  initialMatterId = null,
  onSelectClient,
}) => {
  const [selectedMatterId, setSelectedMatterId] = useState<string | null>(initialMatterId);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "CLOSED">("ALL");

  const { data: matters, isLoading, error } = useQuery<MatterSummaryResponse[]>({
    queryKey: ["matters"],
    queryFn: fetchAllMatters,
  });

  if (selectedMatterId) {
    return (
      <MatterDetailPage
        matterId={selectedMatterId}
        onBack={() => setSelectedMatterId(null)}
        onSelectClient={(cid) => {
          if (onSelectClient) {
            onSelectClient(cid);
          } else {
            setSelectedClientId(cid);
            setSelectedMatterId(null);
          }
        }}
      />
    );
  }

  if (selectedClientId) {
    return (
      <ClientDetailPage
        clientId={selectedClientId}
        onBack={() => setSelectedClientId(null)}
        onSelectMatter={(mid) => {
          setSelectedClientId(null);
          setSelectedMatterId(mid);
        }}
      />
    );
  }

  const filteredMatters = (matters || []).filter((m) => {
    if (statusFilter !== "ALL" && m.status !== statusFilter) {
      return false;
    }
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      m.title.toLowerCase().includes(q) ||
      (m.court_or_forum && m.court_or_forum.toLowerCase().includes(q)) ||
      (m.case_type && m.case_type.toLowerCase().includes(q)) ||
      (m.client_role && m.client_role.toLowerCase().includes(q))
    );
  });

  return (
    <div>
      <PageHeader
        title="Matters"
        description={`${(matters || []).length} total matters`}
      />

      <div
        style={{
          display: "flex",
          gap: "var(--space-3)",
          marginBottom: "var(--space-4)",
          flexWrap: "wrap",
        }}
      >
        <div style={{ maxWidth: "320px", flex: 1 }}>
          <Input
            type="search"
            placeholder="Search matters..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search matters"
          />
        </div>
        <div style={{ width: "160px" }}>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as "ALL" | "ACTIVE" | "CLOSED")}
            options={[
              { value: "ALL", label: "All statuses" },
              { value: "ACTIVE", label: "Active" },
              { value: "CLOSED", label: "Closed" },
            ]}
            aria-label="Filter by status"
          />
        </div>
      </div>

      {isLoading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading matters...</p>
      ) : error ? (
        <p style={{ color: "var(--status-overdue-text)" }}>
          Failed to load matters: {error instanceof Error ? error.message : String(error)}
        </p>
      ) : filteredMatters.length === 0 ? (
        <EmptyState
          message={search || statusFilter !== "ALL" ? "No matters match your filter." : "No matters registered yet."}
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
            {filteredMatters.map((m) => (
              <Tr
                key={m.matter_id}
                clickable
                onClick={() => setSelectedMatterId(m.matter_id)}
              >
                <Td style={{ fontWeight: 500 }}>{m.title}</Td>
                <Td style={{ color: "var(--text-muted)" }}>{m.case_type || "—"}</Td>
                <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                  {m.court_or_forum || "—"}
                </Td>
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
  );
};
