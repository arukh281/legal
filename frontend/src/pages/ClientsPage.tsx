import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchClients,
  createClient,
  type ClientCreateRequest,
} from "../api/client";

interface ClientsPageProps {
  onSelectClient: (clientId: string) => void;
}

export const ClientsPage: React.FC<ClientsPageProps> = ({ onSelectClient }) => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [clientType, setClientType] = useState("COMPANY");
  const [cin, setCin] = useState("");
  const [pan, setPan] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [notes, setNotes] = useState("");

  const { data: clients, isLoading, error } = useQuery({
    queryKey: ["clients"],
    queryFn: fetchClients,
  });

  const createMutation = useMutation({
    mutationFn: (data: ClientCreateRequest) => createClient(data),
    onSuccess: (newClient) => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      setShowCreateModal(false);
      resetForm();
      onSelectClient(newClient.client_id);
    },
  });

  const resetForm = () => {
    setName("");
    setClientType("COMPANY");
    setCin("");
    setPan("");
    setContactName("");
    setContactEmail("");
    setContactPhone("");
    setNotes("");
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const identifiers: Record<string, string> = {};
    if (cin.trim()) identifiers.CIN = cin.trim();
    if (pan.trim()) identifiers.PAN = pan.trim();

    const contact: Record<string, string> = {};
    if (contactName.trim()) contact.name = contactName.trim();
    if (contactEmail.trim()) contact.email = contactEmail.trim();
    if (contactPhone.trim()) contact.phone = contactPhone.trim();

    createMutation.mutate({
      display_name: name.trim(),
      client_type: clientType,
      identifiers,
      contact,
      notes: notes.trim() || undefined,
    });
  };

  const filteredClients = (clients || []).filter((c) => {
    const q = search.toLowerCase();
    return (
      c.display_name.toLowerCase().includes(q) ||
      c.client_type.toLowerCase().includes(q) ||
      (c.notes && c.notes.toLowerCase().includes(q))
    );
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
          <h1 style={{ fontSize: "24px", fontWeight: "700", margin: 0 }}>Clients</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px", fontSize: "14px" }}>
            Firm client directory and case files
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
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
          + New Client
        </button>
      </div>

      {/* Search Bar */}
      <div style={{ marginBottom: "20px" }}>
        <input
          type="text"
          placeholder="Search clients by name, type, notes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "12px 16px",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            backgroundColor: "var(--bg-secondary)",
            color: "var(--text-primary)",
            fontSize: "14px",
          }}
        />
      </div>

      {/* Content */}
      {isLoading ? (
        <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading clients...
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
          Failed to load clients: {(error as Error).message}
        </div>
      ) : filteredClients.length === 0 ? (
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
            No clients found
          </p>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "20px" }}>
            {search ? "No clients match your search query." : "Create your first client to start organizing matters."}
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              backgroundColor: "var(--accent)",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            + Create Client
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gap: "12px" }}>
          {filteredClients.map((client) => {
            const contact = client.contact as Record<string, string>;
            const ids = client.identifiers as Record<string, string>;
            return (
              <div
                key={client.client_id}
                onClick={() => onSelectClient(client.client_id)}
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
                  transition: "border-color 0.15s ease",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "16px", fontWeight: "600" }}>
                      {client.display_name}
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: "600",
                        padding: "2px 8px",
                        borderRadius: "12px",
                        backgroundColor: "var(--bg-tertiary)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {client.client_type}
                    </span>
                    {client.status === "ARCHIVED" && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: "600",
                          padding: "2px 8px",
                          borderRadius: "12px",
                          backgroundColor: "#fef3c7",
                          color: "#92400e",
                        }}
                      >
                        Archived
                      </span>
                    )}
                  </div>

                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "16px",
                      marginTop: "6px",
                      fontSize: "13px",
                      color: "var(--text-muted)",
                    }}
                  >
                    {contact.email && <span>✉️ {contact.email}</span>}
                    {contact.phone && <span>📞 {contact.phone}</span>}
                    {ids.CIN && <span>CIN: {ids.CIN}</span>}
                    {ids.PAN && <span>PAN: {ids.PAN}</span>}
                  </div>
                </div>

                <div style={{ color: "var(--text-muted)", fontSize: "18px" }}>→</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Client Modal */}
      {showCreateModal && (
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
              <h2 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>New Client</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Client Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Steel Pvt Ltd"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
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
                  Client Type
                </label>
                <select
                  value={clientType}
                  onChange={(e) => setClientType(e.target.value)}
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
                  <option value="COMPANY">Company</option>
                  <option value="INDIVIDUAL">Individual</option>
                  <option value="LLP">LLP</option>
                  <option value="PARTNERSHIP">Partnership</option>
                  <option value="GOVERNMENT">Government</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    CIN (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="U12345MH2020PTC123456"
                    value={cin}
                    onChange={(e) => setCin(e.target.value)}
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
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    PAN (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="AAACA1234A"
                    value={pan}
                    onChange={(e) => setPan(e.target.value)}
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

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Primary Contact Details
                </label>
                <div style={{ display: "grid", gap: "8px" }}>
                  <input
                    type="text"
                    placeholder="Contact Name"
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
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
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                    <input
                      type="email"
                      placeholder="Email"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
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
                    <input
                      type="tel"
                      placeholder="Phone"
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
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
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Internal notes regarding this client relationship..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-secondary)",
                    color: "var(--text-primary)",
                    resize: "vertical",
                  }}
                />
              </div>

              {createMutation.isError && (
                <div style={{ color: "var(--danger)", fontSize: "13px", marginBottom: "12px" }}>
                  Error: {(createMutation.error as Error).message}
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
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
                  disabled={createMutation.isPending}
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
                  {createMutation.isPending ? "Creating..." : "Save Client"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
