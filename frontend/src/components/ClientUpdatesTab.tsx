import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMatterClientUpdates,
  fetchMatterClientUpdateDraft,
  createMatterClientUpdate,
  fetchMatterShareLink,
  type ClientUpdateResponse,
  type ClientUpdateDraftResponse,
} from "../api/client";
import { ShareLinkModal } from "./ShareLinkModal";

interface ClientUpdatesTabProps {
  matterId: string;
  matterTitle: string;
}

export const ClientUpdatesTab: React.FC<ClientUpdatesTabProps> = ({
  matterId,
  matterTitle,
}) => {
  const queryClient = useQueryClient();
  const [showShareModal, setShowShareModal] = useState(false);
  const [draft, setDraft] = useState<ClientUpdateDraftResponse | null>(null);
  const [draftText, setDraftText] = useState("");
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [copiedUpdateId, setCopiedUpdateId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: updates, isLoading: updatesLoading } = useQuery<ClientUpdateResponse[]>({
    queryKey: ["matter_client_updates", matterId],
    queryFn: () => fetchMatterClientUpdates(matterId),
  });

  const { data: shareLink } = useQuery({
    queryKey: ["matter_share_link", matterId],
    queryFn: async () => {
      try {
        return await fetchMatterShareLink(matterId);
      } catch {
        return null;
      }
    },
  });

  const handleGenerateDraft = async () => {
    setIsGeneratingDraft(true);
    setActionError(null);
    try {
      const res = await fetchMatterClientUpdateDraft(matterId);
      setDraft(res);
      setDraftText(res.draft_text);
    } catch (err: any) {
      setActionError(err.message || "Failed to generate update draft.");
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  const publishMutation = useMutation({
    mutationFn: () =>
      createMatterClientUpdate(matterId, {
        text: draftText.trim(),
        facts: (draft?.facts as any) || {},
      }),
    onSuccess: () => {
      setDraft(null);
      setDraftText("");
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["matter_client_updates", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
    },
    onError: (err: any) => {
      setActionError(err.message || "Failed to publish client update.");
    },
  });

  const handleCopyUpdateText = (updateText: string, updateId: string) => {
    const title = shareLink?.client_matter_title || matterTitle;
    const formatted = `*Update: ${title}*\n\n${updateText}`;
    navigator.clipboard.writeText(formatted);
    setCopiedUpdateId(updateId);
    setTimeout(() => setCopiedUpdateId(null), 2500);
  };

  return (
    <div>
      {/* Top action header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "24px",
          paddingBottom: "16px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div>
          <h3 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Client Updates</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginTop: "4px" }}>
            Publish progress reports and send WhatsApp-ready updates with public status links.
          </p>
        </div>

        <button
          onClick={() => setShowShareModal(true)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 16px",
            borderRadius: "6px",
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border)",
            color: "var(--text-primary)",
            fontSize: "13px",
            fontWeight: "600",
            cursor: "pointer",
            minHeight: "40px",
          }}
        >
          <span>🔗</span> Manage Share Link
        </button>
      </div>

      {actionError && (
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
          {actionError}
        </div>
      )}

      {/* Draft section */}
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "32px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "14px",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div>
            <div style={{ fontSize: "15px", fontWeight: "700" }}>Draft New Update</div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Auto-generate from recent hearings, filings, and court orders
            </div>
          </div>

          <button
            onClick={handleGenerateDraft}
            disabled={isGeneratingDraft}
            style={{
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
            {isGeneratingDraft ? "Generating Draft..." : "✨ Generate Draft"}
          </button>
        </div>

        {draft && (
          <div style={{ marginTop: "16px" }}>
            {/* Extracted Facts Overview */}
            {draft.facts && Object.keys(draft.facts).length > 0 && (
              <div
                style={{
                  backgroundColor: "rgba(59, 130, 246, 0.08)",
                  border: "1px solid rgba(59, 130, 246, 0.25)",
                  borderRadius: "8px",
                  padding: "12px 16px",
                  marginBottom: "14px",
                  fontSize: "12px",
                }}
              >
                <div style={{ fontWeight: "700", color: "var(--accent)", marginBottom: "4px" }}>
                  Extracted Record Facts:
                </div>
                {Boolean((draft.facts as any).last_hearing) && (
                  <div>
                    • Last Hearing: {(draft.facts as any).last_hearing.date} (
                    {(draft.facts as any).last_hearing.status}
                    {(draft.facts as any).last_hearing.outcome
                      ? ` - ${(draft.facts as any).last_hearing.outcome}`
                      : ""}
                    )
                  </div>
                )}
                {Boolean((draft.facts as any).next_hearing) && (
                  <div>• Next Scheduled Date: {(draft.facts as any).next_hearing.date}</div>
                )}
                {Boolean((draft.facts as any).recent_documents_count) && (
                  <div>• Filings Filed: {(draft.facts as any).recent_documents_count} document(s)</div>
                )}
              </div>
            )}

            <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "6px" }}>
              Update Text (Review and edit before publishing)
            </label>
            <textarea
              rows={5}
              value={draftText}
              onChange={(e) => setDraftText(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "6px",
                border: "1px solid var(--border)",
                backgroundColor: "var(--bg-primary)",
                color: "var(--text-primary)",
                fontSize: "13px",
                lineHeight: "1.5",
                resize: "vertical",
              }}
            />

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px" }}>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                ⚠️ Published updates are immutable snapshots on the firm ledger.
              </span>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => {
                    setDraft(null);
                    setDraftText("");
                  }}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    background: "none",
                    cursor: "pointer",
                    fontSize: "12px",
                  }}
                >
                  Discard
                </button>
                <button
                  type="button"
                  onClick={() => publishMutation.mutate()}
                  disabled={publishMutation.isPending || !draftText.trim()}
                  style={{
                    padding: "8px 20px",
                    borderRadius: "6px",
                    backgroundColor: "var(--success)",
                    color: "#fff",
                    border: "none",
                    fontWeight: "600",
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  {publishMutation.isPending ? "Publishing..." : "Publish Update"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Published Updates History */}
      <div>
        <h4 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "14px" }}>
          Published Updates History ({(updates || []).length})
        </h4>

        {updatesLoading ? (
          <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)" }}>
            Loading updates...
          </div>
        ) : !updates || updates.length === 0 ? (
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px dashed var(--border)",
              borderRadius: "10px",
              padding: "36px",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "14px",
            }}
          >
            No client updates have been published for this matter yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {updates.map((update) => (
              <div
                key={update.update_id}
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "16px 20px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "10px",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}
                >
                  <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    Published on{" "}
                    <strong>{new Date(update.published_at).toLocaleString("en-IN")}</strong> by{" "}
                    {update.published_by}
                  </div>

                  <button
                    onClick={() => handleCopyUpdateText(update.text, update.update_id)}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--border)",
                      backgroundColor:
                        copiedUpdateId === update.update_id
                          ? "rgba(16, 185, 129, 0.15)"
                          : "var(--bg-primary)",
                      color:
                        copiedUpdateId === update.update_id
                          ? "var(--success)"
                          : "var(--text-primary)",
                      fontSize: "12px",
                      fontWeight: "600",
                      cursor: "pointer",
                      minHeight: "36px",
                    }}
                  >
                    <span>{copiedUpdateId === update.update_id ? "✓" : "📋"}</span>
                    <span>
                      {copiedUpdateId === update.update_id ? "Copied!" : "Copy update text"}
                    </span>
                  </button>
                </div>

                <div
                  style={{
                    fontSize: "14px",
                    color: "var(--text-primary)",
                    lineHeight: "1.6",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {update.text}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Share Link Modal */}
      {showShareModal && (
        <ShareLinkModal
          matterId={matterId}
          matterTitle={matterTitle}
          onClose={() => {
            setShowShareModal(false);
            queryClient.invalidateQueries({ queryKey: ["matter_share_link", matterId] });
          }}
        />
      )}
    </div>
  );
};
