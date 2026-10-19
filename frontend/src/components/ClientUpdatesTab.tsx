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
import {
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  EmptyState,
} from "./ui";
import { formatDate } from "../utils/format";

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
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to generate update draft.");
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  const publishMutation = useMutation({
    mutationFn: () =>
      createMatterClientUpdate(matterId, {
        text: draftText.trim(),
        facts: (draft?.facts as Record<string, unknown>) || {},
      }),
    onSuccess: () => {
      setDraft(null);
      setDraftText("");
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["matter_client_updates", matterId] });
      queryClient.invalidateQueries({ queryKey: ["matter_timeline", matterId] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to publish client update.");
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
      {/* Top action bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "var(--space-3)",
          marginBottom: "var(--space-4)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowShareModal(true)}
          >
            Client status link
          </Button>
          {shareLink && !shareLink.revoked_at && (
            <Badge variant="done">Link active</Badge>
          )}
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleGenerateDraft}
          disabled={isGeneratingDraft}
        >
          {isGeneratingDraft ? "Generating draft..." : "Draft update"}
        </Button>
      </div>

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

      {/* Draft editor */}
      {draft && (
        <div
          style={{
            backgroundColor: "var(--bg-subtle)",
            border: "1px solid var(--border-main)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-4)",
            marginBottom: "var(--space-6)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
            <span style={{ fontSize: "var(--text-base)", fontWeight: 600 }}>Draft client update</span>
            <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
              Assembled from matter records
            </span>
          </div>

          <textarea
            className="textarea"
            rows={5}
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            style={{ marginBottom: "var(--space-3)" }}
          />

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-2)" }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setDraft(null);
                setDraftText("");
              }}
            >
              Discard
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => publishMutation.mutate()}
              disabled={publishMutation.isPending || !draftText.trim()}
            >
              {publishMutation.isPending ? "Publishing..." : "Publish update"}
            </Button>
          </div>
        </div>
      )}

      {/* Published updates history */}
      <div>
        <h3 style={{ fontSize: "var(--text-base)", fontWeight: 600, marginBottom: "var(--space-3)" }}>
          Published updates ({(updates || []).length})
        </h3>

        {updatesLoading ? (
          <p style={{ color: "var(--text-muted)" }}>Loading updates...</p>
        ) : (updates || []).length === 0 ? (
          <EmptyState
            message="No published updates yet. Generate a draft to communicate matter status to the client."
          />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th style={{ width: "120px" }}>Date</Th>
                <Th>Update message</Th>
                <Th style={{ width: "160px" }}>Published by</Th>
                <Th style={{ width: "90px" }}></Th>
              </Tr>
            </Thead>
            <Tbody>
              {(updates || []).map((u) => (
                <Tr key={u.update_id}>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {formatDate(u.created_at)}
                  </Td>
                  <Td>
                    <div style={{ whiteSpace: "pre-wrap", fontSize: "var(--text-base)" }}>
                      {u.text}
                    </div>
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {u.published_by || "Partner"}
                  </Td>
                  <Td>
                    <Button
                      variant="quiet"
                      size="sm"
                      onClick={() => handleCopyUpdateText(u.text, u.update_id)}
                    >
                      {copiedUpdateId === u.update_id ? "Copied" : "Copy"}
                    </Button>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </div>

      {showShareModal && (
        <ShareLinkModal
          matterId={matterId}
          matterTitle={matterTitle}
          onClose={() => setShowShareModal(false)}
        />
      )}
    </div>
  );
};
