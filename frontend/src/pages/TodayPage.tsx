import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchToday,
  updateTaskStatus,
  getFirmCalendarExportUrl,
  type TodayResponse,
  type TodayTaskItem,
  type TodayHearingItem,
} from "../api/client";
import {
  PageHeader,
  Badge,
  EmptyState,
} from "../components/ui";
import { formatDate, formatStatus } from "../utils/format";

interface TodayPageProps {
  onSelectMatter?: (matterId: string) => void;
}

export const TodayPage: React.FC<TodayPageProps> = ({ onSelectMatter }) => {
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useQuery<TodayResponse>({
    queryKey: ["today"],
    queryFn: fetchToday,
    refetchInterval: 30000,
  });

  const taskStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      updateTaskStatus(taskId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to update task.");
    },
  });

  if (isLoading) {
    return (
      <div>
        <p style={{ color: "var(--text-muted)" }}>Loading schedule...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div>
        <p style={{ color: "var(--status-overdue-text)" }}>
          Failed to load: {error instanceof Error ? error.message : String(error)}
        </p>
      </div>
    );
  }

  const formattedToday = formatDate(data.today_date);

  const moreActions = [
    {
      label: "Export calendar (.ics)",
      onClick: () => {
        window.open(getFirmCalendarExportUrl(), "_blank");
      },
    },
    {
      label: "Refresh",
      onClick: () => {
        refetch();
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title="Today"
        description={`${formattedToday} • ${data.total_active_matters} active matters`}
        moreActions={moreActions}
      />

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

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-8)" }}>
        {/* List 1: Hearings today */}
        <section>
          <div style={{ marginBottom: "var(--space-2)" }}>
            <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, color: "var(--text-main)" }}>
              Hearings today ({data.today_hearings.length})
            </h2>
          </div>

          {data.today_hearings.length === 0 ? (
            <EmptyState message="No hearings listed for today." />
          ) : (
            <div className="plain-list">
              {data.today_hearings.map((h: TodayHearingItem) => {
                const itemTime = h.court_no
                  ? (h.court_no.trim().toLowerCase().startsWith("court") ? h.court_no.trim() : `Court ${h.court_no.trim()}`)
                  : "Listed";
                const courtName = h.court_or_forum || "Court";
                const matterName = h.matter_title || "Matter";
                const itemDetails = h.item_no
                  ? `Item ${h.item_no}${h.purpose ? ` • ${formatStatus(h.purpose)}` : ""}`
                  : h.purpose
                  ? formatStatus(h.purpose)
                  : "Scheduled hearing";

                return (
                  <div
                    key={h.hearing_id}
                    className="plain-list-row clickable"
                    onClick={() => onSelectMatter && onSelectMatter(h.matter_id)}
                  >
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                      {itemTime}
                    </span>
                    <span style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {matterName}
                    </span>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {courtName}
                    </span>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {itemDetails}
                      </span>
                      {h.status && h.status !== "LISTED" && (
                        <Badge variant="neutral">{formatStatus(h.status)}</Badge>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* List 2: Tomorrow */}
        <section>
          <div style={{ marginBottom: "var(--space-2)" }}>
            <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, color: "var(--text-main)" }}>
              Tomorrow ({data.tomorrow_hearings.length})
            </h2>
          </div>

          {data.tomorrow_hearings.length === 0 ? (
            <EmptyState message="No hearings listed for tomorrow." />
          ) : (
            <div className="plain-list">
              {data.tomorrow_hearings.map((h: TodayHearingItem) => {
                const itemTime = h.court_no
                  ? (h.court_no.trim().toLowerCase().startsWith("court") ? h.court_no.trim() : `Court ${h.court_no.trim()}`)
                  : "Listed";
                const courtName = h.court_or_forum || "Court";
                const matterName = h.matter_title || "Matter";
                const itemDetails = h.item_no
                  ? `Item ${h.item_no}${h.purpose ? ` • ${formatStatus(h.purpose)}` : ""}`
                  : h.purpose
                  ? formatStatus(h.purpose)
                  : "Scheduled hearing";

                return (
                  <div
                    key={h.hearing_id}
                    className="plain-list-row clickable"
                    onClick={() => onSelectMatter && onSelectMatter(h.matter_id)}
                  >
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                      {itemTime}
                    </span>
                    <span style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {matterName}
                    </span>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {courtName}
                    </span>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {itemDetails}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* List 3: My tasks this week */}
        <section>
          <div style={{ marginBottom: "var(--space-2)" }}>
            <h2 style={{ fontSize: "var(--text-base)", fontWeight: 600, color: "var(--text-main)" }}>
              My tasks this week ({data.my_tasks.length})
            </h2>
          </div>

          {data.my_tasks.length === 0 ? (
            <EmptyState message="No tasks due this week." />
          ) : (
            <div className="plain-list">
              {data.my_tasks.map((t: TodayTaskItem) => {
                const dateText = t.due_on ? formatDate(t.due_on) : "No due date";
                const matterName = t.matter_title || "Matter";
                const courtName = t.assignee_name || "Assigned";
                const isOverdue = t.is_overdue;
                const isDone = t.status === "DONE";

                return (
                  <div
                    key={t.task_id}
                    className="plain-list-row clickable"
                    onClick={() => onSelectMatter && onSelectMatter(t.matter_id)}
                  >
                    <span style={{ fontSize: "var(--text-sm)", color: isOverdue ? "var(--status-overdue-text)" : "var(--text-muted)", fontWeight: isOverdue ? 500 : 400 }}>
                      {dateText}
                    </span>
                    <span style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {matterName}
                    </span>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {courtName}
                    </span>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: "var(--space-2)",
                      }}
                    >
                      <span
                        style={{
                          textDecoration: isDone ? "line-through" : "none",
                          color: isDone ? "var(--text-faint)" : "var(--text-main)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.title}
                      </span>
                      <div
                        style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {isOverdue && !isDone && (
                          <Badge variant="overdue">Overdue</Badge>
                        )}
                        <input
                          type="checkbox"
                          checked={isDone}
                          onChange={(e) => {
                            taskStatusMutation.mutate({
                              taskId: t.task_id,
                              status: e.target.checked ? "DONE" : "OPEN",
                            });
                          }}
                          style={{ cursor: "pointer", accentColor: "var(--accent-main)" }}
                          title={isDone ? "Mark open" : "Mark done"}
                          aria-label={`Toggle task completion for ${t.title}`}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
