import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAllMatters, fetchMe } from "../api/client";
import { MatterDetailPage } from "./MatterDetailPage";
import { ClientDetailPage } from "./ClientDetailPage";
import { ImportCasesPage } from "./ImportCasesPage";

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
  const [showImportPage, setShowImportPage] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "CLOSED">("ALL");

  const { data: currentUser } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });

  const isFirmAdmin = currentUser?.role === "ADMIN";

  const { data: matters, isLoading, error } = useQuery({
    queryKey: ["matters"],
    queryFn: fetchAllMatters,
  });

  if (showImportPage) {
    return <ImportCasesPage onBack={() => setShowImportPage(false)} />;
  }

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
          setSelectedMatterId(mid);
          setSelectedClientId(null);
        }}
      />
    );
  }

  const filteredMatters = (matters || []).filter((m) => {
    const q = search.toLowerCase();
    const matchesSearch =
      m.title.toLowerCase().includes(q) ||
      (m.case_type && m.case_type.toLowerCase().includes(q)) ||
      (m.court_or_forum && m.court_or_forum.toLowerCase().includes(q));

    if (!matchesSearch) return false;
    if (statusFilter === "ACTIVE") return m.status === "ACTIVE";
    if (statusFilter === "CLOSED") return m.status === "CLOSED";
    return true;
  });

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "16px" }}>
      {/* Page Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "24px",
        }}
      >
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: "700", margin: 0 }}>Matters</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px", fontSize: "14px" }}>
            All active and closed case workspaces
          </p>
        </div>

        {isFirmAdmin && (
          <button
            onClick={() => setShowImportPage(true)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "6px",
              backgroundColor: "var(--accent)",
              color: "#fff",
              border: "none",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            <span>📥</span> Import Cases
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "20px",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          placeholder="Search matters by title, case type, court..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            minWidth: "240px",
            boxSizing: "border-box",
            padding: "10px 14px",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            backgroundColor: "var(--bg-secondary)",
            color: "var(--text-primary)",
            fontSize: "14px",
          }}
        />

        <div style={{ display: "flex", gap: "4px", backgroundColor: "var(--bg-secondary)", padding: "4px", borderRadius: "8px", border: "1px solid var(--border)" }}>
          {(["ALL", "ACTIVE", "CLOSED"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              style={{
                padding: "6px 12px",
                border: "none",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: "600",
                backgroundColor: statusFilter === s ? "var(--accent)" : "transparent",
                color: statusFilter === s ? "#fff" : "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              {s === "ALL" ? "All" : s === "ACTIVE" ? "Active" : "Closed"}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading matters...
        </div>
      ) : error ? (
        <div
          style={{
            padding: "20px",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "8px",
            color: "#991b1b",
          }}
        >
          Failed to load matters: {(error as Error).message}
        </div>
      ) : filteredMatters.length === 0 ? (
        <div
          style={{
            padding: "60px 20px",
            textAlign: "center",
            backgroundColor: "var(--bg-secondary)",
            borderRadius: "12px",
            border: "1px dashed var(--border)",
          }}
        >
          <p style={{ fontSize: "16px", fontWeight: "600", marginBottom: "8px" }}>
            No matters found
          </p>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "16px" }}>
            {search ? "No matters match your filter criteria." : "Open a matter from any client file to start working."}
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gap: "10px" }}>
          {filteredMatters.map((matter) => (
            <div
              key={matter.matter_id}
              onClick={() => setSelectedMatterId(matter.matter_id)}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                padding: "16px 20px",
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "16px", fontWeight: "600" }}>{matter.title}</span>
                  {matter.case_type && (
                    <span
                      style={{
                        fontSize: "11px",
                        padding: "2px 8px",
                        borderRadius: "4px",
                        backgroundColor: "var(--bg-tertiary)",
                        color: "var(--text-secondary)",
                        fontWeight: "600",
                      }}
                    >
                      {matter.case_type}
                    </span>
                  )}
                  {matter.court_or_forum && (
                    <span
                      style={{
                        fontSize: "11px",
                        padding: "2px 8px",
                        borderRadius: "4px",
                        backgroundColor: "var(--bg-tertiary)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {matter.court_or_forum}
                    </span>
                  )}
                  {matter.status === "CLOSED" ? (
                    <span
                      style={{
                        fontSize: "11px",
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
                        fontSize: "11px",
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

                <div
                  style={{
                    display: "flex",
                    gap: "14px",
                    marginTop: "6px",
                    fontSize: "12px",
                    color: "var(--text-muted)",
                  }}
                >
                  <span>Role: {matter.client_role}</span>
                  <span>Opened: {new Date(matter.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div style={{ color: "var(--text-muted)", fontSize: "18px" }}>→</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
