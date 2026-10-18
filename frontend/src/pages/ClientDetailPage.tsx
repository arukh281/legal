import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchClient,
  archiveClient,
  createMatter,
  type MatterCreateRequest,
} from "../api/client";

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

  const { data, isLoading, error } = useQuery({
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

  const caseTypeSuggestions = [
    "Insolvency (IBC)",
    "Arbitration",
    "Company law",
    "Cheque bounce (s.138)",
    "Civil suit",
    "Writ",
    "Criminal",
    "Advisory",
  ];

  const courtSuggestions = [
    "NCLT Mumbai",
    "Delhi High Court",
    "Bombay High Court",
    "Supreme Court of India",
    "Arbitral tribunal",
  ];

  if (isLoading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading client file...</div>;
  }

  if (error || !data) {
    return (
      <div style={{ padding: "20px" }}>
        <button onClick={onBack} style={{ marginBottom: "16px", cursor: "pointer" }}>
          ← Back to Clients
        </button>
        <div style={{ color: "var(--danger)" }}>
          Failed to load client: {error ? (error as Error).message : "Not found"}
        </div>
      </div>
    );
  }

  const { client, matters } = data;
  const contact = client.contact as Record<string, string>;
  const ids = client.identifiers as Record<string, string>;

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "16px" }}>
      {/* Navigation Breadcrumb */}
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
        ← Back to Clients
      </button>

      {/* Client File Header */}
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
              <h1 style={{ fontSize: "24px", fontWeight: "700", margin: 0 }}>
                {client.display_name}
              </h1>
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: "600",
                  padding: "2px 8px",
                  borderRadius: "12px",
                  backgroundColor: "var(--bg-tertiary)",
                  color: "var(--text-secondary)",
                }}
              >
                {client.client_type}
              </span>
              {client.status === "ARCHIVED" ? (
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "600",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    backgroundColor: "#fef3c7",
                    color: "#92400e",
                  }}
                >
                  Archived
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
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Client ID: {client.client_id}
            </p>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            {client.status === "ACTIVE" && (
              <button
                onClick={() => {
                  if (confirm("Archive this client?")) {
                    archiveMutation.mutate();
                  }
                }}
                disabled={archiveMutation.isPending}
                style={{
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  background: "none",
                  fontSize: "12px",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                }}
              >
                Archive Client
              </button>
            )}
            <button
              onClick={() => setShowMatterModal(true)}
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
              + Open Matter
            </button>
          </div>
        </div>

        {/* Contact & Identifiers */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
            borderTop: "1px solid var(--border)",
            paddingTop: "16px",
            fontSize: "13px",
          }}
        >
          <div>
            <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px" }}>
              CONTACT
            </span>
            <span>{contact.name || "None listed"}</span>
            {contact.email && <div style={{ color: "var(--text-secondary)" }}>{contact.email}</div>}
            {contact.phone && <div style={{ color: "var(--text-secondary)" }}>{contact.phone}</div>}
          </div>
          <div>
            <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px" }}>
              REGISTRATION / TAX
            </span>
            {ids.CIN && <div>CIN: {ids.CIN}</div>}
            {ids.PAN && <div>PAN: {ids.PAN}</div>}
            {!ids.CIN && !ids.PAN && <span style={{ color: "var(--text-muted)" }}>None provided</span>}
          </div>
          <div>
            <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px" }}>
              NOTES
            </span>
            <span style={{ color: "var(--text-secondary)" }}>{client.notes || "None"}</span>
          </div>
        </div>
      </div>

      {/* Matters Section */}
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>
            Matters ({matters.length})
          </h2>
          <button
            onClick={() => setShowMatterModal(true)}
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
            + New Matter
          </button>
        </div>

        {matters.length === 0 ? (
          <div
            style={{
              padding: "40px 20px",
              textAlign: "center",
              backgroundColor: "var(--bg-secondary)",
              borderRadius: "10px",
              border: "1px dashed var(--border)",
            }}
          >
            <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "12px" }}>
              No matters opened under this client yet.
            </p>
            <button
              onClick={() => setShowMatterModal(true)}
              style={{
                backgroundColor: "var(--accent)",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                padding: "8px 14px",
                fontSize: "13px",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              + Open First Matter
            </button>
          </div>
        ) : (
          <div style={{ display: "grid", gap: "10px" }}>
            {matters.map((matter) => (
              <div
                key={matter.matter_id}
                onClick={() => onSelectMatter(matter.matter_id)}
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  padding: "16px",
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
                    <span style={{ fontSize: "15px", fontWeight: "600" }}>{matter.title}</span>
                    {matter.case_type && (
                      <span
                        style={{
                          fontSize: "11px",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: "var(--bg-tertiary)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {matter.case_type}
                      </span>
                    )}
                    {matter.court_or_forum && (
                      <span
                        style={{
                          fontSize: "11px",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: "var(--bg-tertiary)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {matter.court_or_forum}
                      </span>
                    )}
                  </div>
                  <div
                    style={{
                      marginTop: "4px",
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      display: "flex",
                      gap: "12px",
                    }}
                  >
                    <span>Role: {matter.client_role === "NOT_SET" ? "Not set" : matter.client_role}</span>
                    <span>Status: {matter.status}</span>
                  </div>
                </div>

                <div style={{ color: "var(--text-muted)", fontSize: "18px" }}>→</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Matter Modal */}
      {showMatterModal && (
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
              maxWidth: "540px",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>
                Open Matter for {client.display_name}
              </h2>
              <button
                onClick={() => setShowMatterModal(false)}
                style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleMatterSubmit}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Matter Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme v. Zenith, s.9 petition"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
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

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Case Type (Any court or dispute)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Insolvency (IBC)"
                  value={caseType}
                  onChange={(e) => setCaseType(e.target.value)}
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
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "6px" }}>
                  {caseTypeSuggestions.map((s) => (
                    <button
                      type="button"
                      key={s}
                      onClick={() => setCaseType(s)}
                      style={{
                        padding: "2px 8px",
                        fontSize: "11px",
                        borderRadius: "10px",
                        border: "1px solid var(--border)",
                        backgroundColor: caseType === s ? "var(--accent)" : "var(--bg-secondary)",
                        color: caseType === s ? "#fff" : "var(--text-secondary)",
                        cursor: "pointer",
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Court or Forum
                </label>
                <input
                  type="text"
                  placeholder="e.g. NCLT Mumbai"
                  value={court}
                  onChange={(e) => setCourt(e.target.value)}
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
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "6px" }}>
                  {courtSuggestions.map((c) => (
                    <button
                      type="button"
                      key={c}
                      onClick={() => setCourt(c)}
                      style={{
                        padding: "2px 8px",
                        fontSize: "11px",
                        borderRadius: "10px",
                        border: "1px solid var(--border)",
                        backgroundColor: court === c ? "var(--accent)" : "var(--bg-secondary)",
                        color: court === c ? "#fff" : "var(--text-secondary)",
                        cursor: "pointer",
                      }}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    Client Role
                  </label>
                  <select
                    value={clientRole}
                    onChange={(e) => setClientRole(e.target.value)}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--border)",
                      backgroundColor: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                    }}
                  >
                    <option value="PETITIONER">Petitioner / Applicant</option>
                    <option value="RESPONDENT">Respondent / Defendant</option>
                    <option value="APPELLANT">Appellant</option>
                    <option value="CLAIMANT">Claimant</option>
                    <option value="ADVISORY">Advisory / Corporate</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    Internal File No. (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 2026/ACM-01"
                    value={clientMatterNo}
                    onChange={(e) => setClientMatterNo(e.target.value)}
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
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={walled}
                    onChange={(e) => setWalled(e.target.checked)}
                  />
                  <span>Ethical wall (strictly restricts visibility to assigned matter team)</span>
                </label>
              </div>

              {createMatterMutation.isError && (
                <div style={{ color: "var(--danger)", fontSize: "13px", marginBottom: "12px" }}>
                  Error: {(createMatterMutation.error as Error).message}
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowMatterModal(false)}
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
                  disabled={createMatterMutation.isPending}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "6px",
                    border: "none",
                    backgroundColor: "var(--accent)",
                    color: "#fff",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {createMatterMutation.isPending ? "Opening Matter..." : "Open Matter"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
