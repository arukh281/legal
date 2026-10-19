import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchClients,
  createClient,
  type ClientCreateRequest,
  type ClientResponse,
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
import { formatStatus } from "../utils/format";

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

  const { data: clients, isLoading, error } = useQuery<ClientResponse[]>({
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
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    const contact = (c.contact || {}) as Record<string, string>;
    const ids = (c.identifiers || {}) as Record<string, string>;
    return (
      c.display_name.toLowerCase().includes(q) ||
      c.client_type.toLowerCase().includes(q) ||
      (contact.name && contact.name.toLowerCase().includes(q)) ||
      (contact.email && contact.email.toLowerCase().includes(q)) ||
      (ids.CIN && ids.CIN.toLowerCase().includes(q)) ||
      (ids.PAN && ids.PAN.toLowerCase().includes(q))
    );
  });

  return (
    <div>
      <PageHeader
        title="Clients"
        description={`${(clients || []).length} registered clients`}
        primaryAction={{
          label: "New client",
          onClick: () => setShowCreateModal(true),
        }}
      />

      <div style={{ marginBottom: "var(--space-4)", maxWidth: "320px" }}>
        <Input
          type="search"
          placeholder="Search clients..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search clients"
        />
      </div>

      {isLoading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading clients...</p>
      ) : error ? (
        <p style={{ color: "var(--status-overdue-text)" }}>
          Failed to load clients: {error instanceof Error ? error.message : String(error)}
        </p>
      ) : filteredClients.length === 0 ? (
        <EmptyState
          message={search ? "No clients match your search." : "No clients created yet."}
          action={
            !search ? (
              <Button variant="secondary" size="sm" onClick={() => setShowCreateModal(true)}>
                New client
              </Button>
            ) : undefined
          }
        />
      ) : (
        <Table>
          <Thead>
            <Tr>
              <Th>Client name</Th>
              <Th>Type</Th>
              <Th>Identifiers</Th>
              <Th>Primary contact</Th>
              <Th>Status</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredClients.map((client) => {
              const contact = (client.contact || {}) as Record<string, string>;
              const ids = (client.identifiers || {}) as Record<string, string>;
              const identifierStr = [ids.CIN && `CIN: ${ids.CIN}`, ids.PAN && `PAN: ${ids.PAN}`]
                .filter(Boolean)
                .join(" • ") || "—";
              const contactStr = [contact.name, contact.email || contact.phone]
                .filter(Boolean)
                .join(" • ") || "—";
              const isArchived = client.status === "ARCHIVED";

              return (
                <Tr
                  key={client.client_id}
                  clickable
                  onClick={() => onSelectClient(client.client_id)}
                >
                  <Td style={{ fontWeight: 500 }}>{client.display_name}</Td>
                  <Td style={{ color: "var(--text-muted)" }}>
                    {formatStatus(client.client_type)}
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {identifierStr}
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {contactStr}
                  </Td>
                  <Td>
                    <Badge variant={isArchived ? "neutral" : "done"}>
                      {formatStatus(client.status || "ACTIVE")}
                    </Badge>
                  </Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      )}

      {/* Create Client Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="New client"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateSubmit}
              disabled={createMutation.isPending || !name.trim()}
            >
              {createMutation.isPending ? "Creating..." : "Create client"}
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          {createMutation.error && (
            <p style={{ color: "var(--status-overdue-text)", fontSize: "var(--text-sm)" }}>
              {createMutation.error instanceof Error
                ? createMutation.error.message
                : "Failed to create client"}
            </p>
          )}

          <Input
            label="Client name *"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Acme Corp"
            required
            autoFocus
          />

          <Select
            label="Client type"
            value={clientType}
            onChange={(e) => setClientType(e.target.value)}
            options={[
              { value: "COMPANY", label: "Company" },
              { value: "INDIVIDUAL", label: "Individual" },
              { value: "LLP", label: "LLP" },
              { value: "PARTNERSHIP", label: "Partnership" },
              { value: "TRUST", label: "Trust" },
              { value: "STATUTORY_BODY", label: "Statutory body" },
            ]}
          />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Input
              label="CIN"
              value={cin}
              onChange={(e) => setCin(e.target.value)}
              placeholder="e.g. U72200DL2018PTC..."
            />
            <Input
              label="PAN"
              value={pan}
              onChange={(e) => setPan(e.target.value)}
              placeholder="e.g. AABCA1234F"
            />
          </div>

          <Input
            label="Contact person"
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            placeholder="e.g. Rahul Sharma"
          />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Input
              label="Email"
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              placeholder="rahul@example.com"
            />
            <Input
              label="Phone"
              value={contactPhone}
              onChange={(e) => setContactPhone(e.target.value)}
              placeholder="+91 98765 43210"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea
              className="textarea"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Internal client notes..."
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};
