import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMatterShareLink,
  createMatterShareLink,
  extendMatterShareLink,
  revokeMatterShareLink,
  type ShareLinkResponse,
} from "../api/client";
import {
  Modal,
  Button,
  Input,
  Select,
  Badge,
} from "./ui";
import { formatDate } from "../utils/format";

interface ShareLinkModalProps {
  matterId: string;
  matterTitle: string;
  onClose: () => void;
}

export const ShareLinkModal: React.FC<ShareLinkModalProps> = ({
  matterId,
  matterTitle,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [clientMatterTitle, setClientMatterTitle] = useState(matterTitle);
  const [days, setDays] = useState(90);
  const [createdResult, setCreatedResult] = useState<ShareLinkResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [whatsAppCopied, setWhatsAppCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { data: link, isLoading, refetch } = useQuery<ShareLinkResponse | null>({
    queryKey: ["matter_share_link", matterId],
    queryFn: async () => {
      try {
        return await fetchMatterShareLink(matterId);
      } catch (e: unknown) {
        if (e instanceof Error && (e.message.includes("404") || e.message.includes("not found"))) {
          return null;
        }
        throw e;
      }
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createMatterShareLink(matterId, {
        client_matter_title: clientMatterTitle.trim() || undefined,
        days,
      }),
    onSuccess: (data) => {
      setCreatedResult(data);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ["matter_share_link", matterId] });
      refetch();
    },
    onError: (err: unknown) => {
      setErrorMsg(err instanceof Error ? err.message : "Failed to create share link.");
    },
  });

  const extendMutation = useMutation({
    mutationFn: (extDays: number) => extendMatterShareLink(matterId, extDays),
    onSuccess: () => {
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ["matter_share_link", matterId] });
      refetch();
    },
    onError: (err: unknown) => {
      setErrorMsg(err instanceof Error ? err.message : "Failed to extend share link.");
    },
  });

  const revokeMutation = useMutation({
    mutationFn: () => revokeMatterShareLink(matterId),
    onSuccess: () => {
      setErrorMsg(null);
      setCreatedResult(null);
      queryClient.invalidateQueries({ queryKey: ["matter_share_link", matterId] });
      refetch();
    },
    onError: (err: unknown) => {
      setErrorMsg(err instanceof Error ? err.message : "Failed to revoke share link.");
    },
  });

  const currentLink = createdResult || link;
  const isRevoked = Boolean(currentLink?.revoked_at);
  const isExpired = currentLink?.expires_at ? new Date(currentLink.expires_at).getTime() < Date.now() : false;
  const isActive = currentLink && !isRevoked && !isExpired;

  const handleCopyLink = () => {
    if (!currentLink?.url) return;
    const fullUrl = window.location.origin + currentLink.url;
    navigator.clipboard.writeText(fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleCopyWhatsAppSnippet = () => {
    if (!currentLink?.url) return;
    const fullUrl = window.location.origin + currentLink.url;
    const title = currentLink.client_matter_title || matterTitle;
    const expiry = currentLink.expires_at ? formatDate(currentLink.expires_at) : "";
    const text = `Matter status link for ${title}:\n${fullUrl}\n\n(Link is read-only and expires on ${expiry})`;
    navigator.clipboard.writeText(text);
    setWhatsAppCopied(true);
    setTimeout(() => setWhatsAppCopied(false), 2500);
  };

  return (
    <Modal isOpen onClose={onClose} title="Client status link">
      {errorMsg && (
        <div
          style={{
            backgroundColor: "var(--status-overdue-bg)",
            border: "1px solid var(--status-overdue-border)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-2) var(--space-3)",
            color: "var(--status-overdue-text)",
            fontSize: "var(--text-sm)",
          }}
        >
          {errorMsg}
        </div>
      )}

      {isLoading ? (
        <p style={{ color: "var(--text-muted)" }}>Checking active links...</p>
      ) : isActive ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Status</span>
            <Badge variant="done">Active</Badge>
          </div>

          <div className="form-group">
            <label className="form-label">Client matter title</label>
            <div style={{ fontSize: "var(--text-base)", fontWeight: 500 }}>
              {currentLink.client_matter_title || matterTitle}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Expires on</label>
            <div style={{ fontSize: "var(--text-base)" }}>
              {currentLink.expires_at ? formatDate(currentLink.expires_at) : "—"}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Shareable URL</label>
            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <Input
                readOnly
                value={window.location.origin + currentLink.url}
                style={{ fontSize: "var(--text-sm)" }}
              />
              <Button variant="secondary" size="sm" onClick={handleCopyLink}>
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>
          </div>

          <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
            <Button variant="secondary" size="sm" onClick={handleCopyWhatsAppSnippet}>
              {whatsAppCopied ? "Snippet copied" : "Copy text snippet"}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => extendMutation.mutate(30)}
              disabled={extendMutation.isPending}
            >
              Extend by 30 days
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => revokeMutation.mutate()}
              disabled={revokeMutation.isPending}
            >
              Revoke link
            </Button>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          {isRevoked ? (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                Previous link was revoked
              </span>
              <Badge variant="overdue">Revoked</Badge>
            </div>
          ) : isExpired ? (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                Previous link has expired
              </span>
              <Badge variant="neutral">Expired</Badge>
            </div>
          ) : (
            <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
              Create a secure, read-only status link for this matter. Clients can view hearing dates,
              next steps, and published updates without firm login.
            </p>
          )}

          <Input
            label="Client-facing matter title"
            value={clientMatterTitle}
            onChange={(e) => setClientMatterTitle(e.target.value)}
            placeholder="Title displayed to client"
          />

          <Select
            label="Validity period"
            value={String(days)}
            onChange={(e) => setDays(Number(e.target.value))}
            options={[
              { value: "30", label: "30 days" },
              { value: "60", label: "60 days" },
              { value: "90", label: "90 days (default)" },
              { value: "180", label: "180 days" },
              { value: "365", label: "1 year" },
            ]}
          />

          <div style={{ marginTop: "var(--space-2)", display: "flex", justifyContent: "flex-end", gap: "var(--space-2)" }}>
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !clientMatterTitle.trim()}
            >
              {createMutation.isPending ? "Generating..." : "Generate link"}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};
