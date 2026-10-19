import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMatterShareLink,
  createMatterShareLink,
  extendMatterShareLink,
  revokeMatterShareLink,
  type ShareLinkResponse,
} from "../api/client";

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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const copyWhatsAppWithLink = () => {
    const title = createdResult?.client_matter_title || clientMatterTitle.trim() || matterTitle;
    const formatted = `*Update: ${title}*\n\nView case status: ${fullShareUrl}`;
    navigator.clipboard.writeText(formatted);
    setWhatsAppCopied(true);
    setTimeout(() => setWhatsAppCopied(false), 2500);
  };

  const isExpired = link && new Date(link.expires_at) < new Date();
  const isRevoked = Boolean(link?.revoked_at);
  const isActive = Boolean(link && !isExpired && !isRevoked);

  const fullShareUrl = createdResult?.url
    ? `${window.location.origin}${createdResult.url}`
    : link?.url
    ? `${window.location.origin}${link.url}`
    : "";

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(2px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "16px",
      }}
    >
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          width: "100%",
          maxWidth: "560px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "20px" }}>🔗</span>
            <h3 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Client Share Link</h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "18px",
              cursor: "pointer",
              color: "var(--text-muted)",
            }}
          >
            ✕
          </button>
        </div>

        {errorMsg && (
          <div
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              border: "1px solid var(--danger)",
              borderRadius: "8px",
              padding: "10px 14px",
              color: "var(--danger)",
              fontSize: "13px",
              marginBottom: "16px",
            }}
          >
            {errorMsg}
          </div>
        )}

        {/* Newly created token view (shown once) */}
        {createdResult?.token && (
          <div
            style={{
              backgroundColor: "rgba(16, 185, 129, 0.12)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              borderRadius: "8px",
              padding: "16px",
              marginBottom: "20px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--success)", fontWeight: "700", fontSize: "14px", marginBottom: "6px" }}>
              <span>✓</span> Share Link Created Successfully
            </div>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: "0 0 12px 0" }}>
              Copy this link now. For security, the secret token will not be shown again.
            </p>
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                type="text"
                readOnly
                value={fullShareUrl}
                style={{
                  flex: 1,
                  padding: "8px 10px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                }}
              />
              <button
                onClick={() => copyToClipboard(fullShareUrl)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  backgroundColor: copied ? "var(--success)" : "var(--accent)",
                  color: "#fff",
                  border: "none",
                  fontWeight: "600",
                  fontSize: "13px",
                  cursor: "pointer",
                  minWidth: "90px",
                }}
              >
                {copied ? "Copied!" : "Copy URL"}
              </button>
            </div>
            <div style={{ marginTop: "10px" }}>
              <button
                onClick={copyWhatsAppWithLink}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  backgroundColor: whatsAppCopied ? "var(--success)" : "rgba(37, 211, 102, 0.15)",
                  color: whatsAppCopied ? "#fff" : "#25D366",
                  border: "1px solid rgba(37, 211, 102, 0.3)",
                  fontWeight: "600",
                  fontSize: "13px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>{whatsAppCopied ? "✓" : "💬"}</span>
                <span>{whatsAppCopied ? "Copied!" : "Copy for WhatsApp (with link)"}</span>
              </button>
            </div>
          </div>
        )}

        {isLoading ? (
          <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)" }}>
            Checking share link status...
          </div>
        ) : isActive ? (
          /* Active share link view */
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div
              style={{
                backgroundColor: "var(--bg-primary)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Status
                </span>
                <span
                  style={{
                    backgroundColor: "rgba(16, 185, 129, 0.15)",
                    color: "var(--success)",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    fontSize: "12px",
                    fontWeight: "600",
                  }}
                >
                  Active
                </span>
              </div>

              <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)", marginBottom: "4px" }}>
                {link?.client_matter_title}
              </div>

              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>
                Expires on: {link ? new Date(link.expires_at).toLocaleDateString() : ""}
              </div>

              {/* URL with copy button */}
              {fullShareUrl && (
                <div style={{ display: "flex", gap: "8px" }}>
                  <input
                    type="text"
                    readOnly
                    value={fullShareUrl}
                    style={{
                      flex: 1,
                      padding: "8px 10px",
                      borderRadius: "6px",
                      border: "1px solid var(--border)",
                      backgroundColor: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      fontSize: "13px",
                    }}
                  />
                  <button
                    onClick={() => copyToClipboard(fullShareUrl)}
                    style={{
                      padding: "8px 14px",
                      borderRadius: "6px",
                      backgroundColor: copied ? "var(--success)" : "var(--accent)",
                      color: "#fff",
                      border: "none",
                      fontWeight: "600",
                      fontSize: "13px",
                      cursor: "pointer",
                      minWidth: "80px",
                    }}
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
              )}
            </div>

            {/* Actions: Extend & Revoke */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={() => extendMutation.mutate(30)}
                  disabled={extendMutation.isPending}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  +30 Days
                </button>
                <button
                  onClick={() => extendMutation.mutate(90)}
                  disabled={extendMutation.isPending}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  +90 Days
                </button>
              </div>

              <button
                onClick={() => {
                  if (window.confirm("Are you sure you want to revoke this share link? The client will no longer be able to view updates via this URL.")) {
                    revokeMutation.mutate();
                  }
                }}
                disabled={revokeMutation.isPending}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  border: "1px solid var(--danger)",
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  color: "var(--danger)",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                {revokeMutation.isPending ? "Revoking..." : "Revoke Link"}
              </button>
            </div>
          </div>
        ) : (
          /* Create new link form */
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate();
            }}
            style={{ display: "flex", flexDirection: "column", gap: "14px" }}
          >
            {isRevoked && (
              <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                The previous share link for this matter was revoked. You can create a new one below.
              </div>
            )}
            {isExpired && (
              <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                The previous share link has expired. Create a new link to restore client access.
              </div>
            )}

            <div>
              <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                Client Matter Title *
              </label>
              <input
                type="text"
                required
                value={clientMatterTitle}
                onChange={(e) => setClientMatterTitle(e.target.value)}
                placeholder="e.g. In the matter of ABC Ltd."
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
              <span style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                This is the heading the client sees on their read-only status page.
              </span>
            </div>

            <div>
              <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "6px" }}>
                Validity Period
              </label>
              <div style={{ display: "flex", gap: "16px", fontSize: "13px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                  <input
                    type="radio"
                    name="days"
                    checked={days === 30}
                    onChange={() => setDays(30)}
                  />
                  30 Days
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                  <input
                    type="radio"
                    name="days"
                    checked={days === 90}
                    onChange={() => setDays(90)}
                  />
                  90 Days (Recommended)
                </label>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
              <button
                type="button"
                onClick={onClose}
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
                disabled={createMutation.isPending || !clientMatterTitle.trim()}
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
                {createMutation.isPending ? "Generating..." : "Generate Share Link"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
