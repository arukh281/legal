import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchToday,
  confirmCandidate,
  dismissCandidate,
  updateDeadlineLifecycle,
  updateTaskStatus,
  getFirmCalendarExportUrl,
  type TodayResponse,
  type TodayTaskItem,
  type CaseCandidateResponse,
  type TodayHearingItem,
  type TodayDeadlineItem,
  type CourtOrderResponse,
} from "../api/client";

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

  const confirmMutation = useMutation({
    mutationFn: (candidateId: string) => confirmCandidate(candidateId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to confirm match.");
    },
  });

  const dismissMutation = useMutation({
    mutationFn: (candidateId: string) => dismissCandidate(candidateId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to dismiss candidate.");
    },
  });

  const deadlineLifecycleMutation = useMutation({
    mutationFn: ({ deadlineId, lifecycle }: { deadlineId: string; lifecycle: string }) =>
      updateDeadlineLifecycle(deadlineId, lifecycle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
  });

  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());

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
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "16px 0" }}>
        <p style={{ color: "var(--text-secondary)" }}>Loading Today's schedule...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "16px 0" }}>
        <p style={{ color: "var(--danger)" }}>Failed to load Today: {error instanceof Error ? error.message : String(error)}</p>
        <button
          onClick={() => refetch()}
          style={{
            marginTop: "12px",
            padding: "8px 16px",
            borderRadius: "6px",
            backgroundColor: "var(--accent)",
            color: "#fff",
            fontWeight: "600",
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  const formattedDate = new Date(data.today_date + "T00:00:00").toLocaleDateString("en-IN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div style={{ maxWidth: "880px", margin: "0 auto", padding: "8px 0 40px 0" }}>
      {/* Top Header / Actions */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
          marginBottom: "28px",
          borderBottom: "1px solid var(--border)",
          paddingBottom: "20px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 style={{ fontSize: "26px", fontWeight: "700", letterSpacing: "-0.02em" }}>Today</h2>
            <span
              style={{
                fontSize: "12px",
                fontWeight: "600",
                color: "var(--accent)",
                backgroundColor: "rgba(59, 130, 246, 0.12)",
                padding: "2px 8px",
                borderRadius: "12px",
              }}
            >
              IST
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px", fontSize: "15px" }}>
            {formattedDate} • {data.total_active_matters} active matters
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <a
            href={getFirmCalendarExportUrl()}
            download="lawyer_brain_calendar.ics"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 16px",
              borderRadius: "8px",
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              fontSize: "13px",
              fontWeight: "600",
              textDecoration: "none",
              cursor: "pointer",
              minHeight: "44px",
            }}
          >
            <span>📅</span> Export Calendar (.ics)
          </a>
          <button
            onClick={() => refetch()}
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
              minHeight: "44px",
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {actionError && (
        <div
          style={{
            backgroundColor: "rgba(239, 68, 68, 0.15)",
            border: "1px solid var(--danger)",
            borderRadius: "8px",
            padding: "12px 16px",
            color: "var(--danger)",
            fontSize: "13px",
            marginBottom: "20px",
          }}
        >
          {actionError}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
        {/* Section 1: Today's Hearings */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>🏛️</span> Listed Today ({data.today_hearings.length})
            </h3>
          </div>

          {data.today_hearings.length === 0 ? (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px dashed var(--border)",
                borderRadius: "10px",
                padding: "24px",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No hearings listed for today.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {data.today_hearings.map((h) => (
                <HearingCard key={h.hearing_id} hearing={h} onSelectMatter={onSelectMatter} isToday />
              ))}
            </div>
          )}
        </section>

        {/* Section 2: Tomorrow's Hearings */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>🌅</span> Listed Tomorrow ({data.tomorrow_hearings.length})
            </h3>
          </div>

          {data.tomorrow_hearings.length === 0 ? (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px dashed var(--border)",
                borderRadius: "10px",
                padding: "20px",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No hearings listed for tomorrow.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {data.tomorrow_hearings.map((h) => (
                <HearingCard key={h.hearing_id} hearing={h} onSelectMatter={onSelectMatter} />
              ))}
            </div>
          )}
        </section>

        {/* Section 3: Check these (Pending Matches / Dropped Notices) */}
        {data.pending_candidates.length > 0 && (
          <section
            style={{
              backgroundColor: "rgba(245, 158, 11, 0.08)",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              borderRadius: "12px",
              padding: "20px",
            }}
          >
            <div style={{ marginBottom: "14px" }}>
              <h3 style={{ fontSize: "18px", fontWeight: "700", color: "#f59e0b", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>⚠️</span> Check these ({data.pending_candidates.length})
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
                Candidate matches from daily NCLT cause lists and IBBI orders requiring your confirmation.
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {data.pending_candidates.map((c) => (
                <CandidateCard
                  key={c.candidate_id}
                  candidate={c}
                  onConfirm={() => confirmMutation.mutate(c.candidate_id)}
                  onDismiss={() => dismissMutation.mutate(c.candidate_id)}
                  isConfirming={confirmMutation.isPending}
                  isDismissing={dismissMutation.isPending}
                  onSelectMatter={onSelectMatter}
                />
              ))}
            </div>
          </section>
        )}

        {/* Section: My Tasks */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>📋</span> My Tasks ({(data.my_tasks || []).length})
            </h3>
          </div>

          {(!data.my_tasks || data.my_tasks.length === 0) ? (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px dashed var(--border)",
                borderRadius: "10px",
                padding: "20px",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No pending tasks assigned to you.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Overdue */}
              {data.my_tasks.some((t) => t.bucket === "OVERDUE") && (
                <div>
                  <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--danger)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
                    ⚠️ Overdue
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {data.my_tasks
                      .filter((t) => t.bucket === "OVERDUE")
                      .map((task) => (
                        <TaskCard
                          key={task.task_id}
                          task={task}
                          isDone={task.status === "DONE" || completedTaskIds.has(task.task_id)}
                          onToggle={() => {
                            const isDone = task.status === "DONE" || completedTaskIds.has(task.task_id);
                            const nextStatus = isDone ? "PENDING" : "DONE";
                            if (nextStatus === "DONE") {
                              setCompletedTaskIds((prev) => new Set(prev).add(task.task_id));
                            } else {
                              setCompletedTaskIds((prev) => {
                                const s = new Set(prev);
                                s.delete(task.task_id);
                                return s;
                              });
                            }
                            taskStatusMutation.mutate({ taskId: task.task_id, status: nextStatus });
                          }}
                          onSelectMatter={onSelectMatter}
                        />
                      ))}
                  </div>
                </div>
              )}

              {/* Today */}
              {data.my_tasks.some((t) => t.bucket === "TODAY") && (
                <div>
                  <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
                    ⭐ Today
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {data.my_tasks
                      .filter((t) => t.bucket === "TODAY")
                      .map((task) => (
                        <TaskCard
                          key={task.task_id}
                          task={task}
                          isDone={task.status === "DONE" || completedTaskIds.has(task.task_id)}
                          onToggle={() => {
                            const isDone = task.status === "DONE" || completedTaskIds.has(task.task_id);
                            const nextStatus = isDone ? "PENDING" : "DONE";
                            if (nextStatus === "DONE") {
                              setCompletedTaskIds((prev) => new Set(prev).add(task.task_id));
                            } else {
                              setCompletedTaskIds((prev) => {
                                const s = new Set(prev);
                                s.delete(task.task_id);
                                return s;
                              });
                            }
                            taskStatusMutation.mutate({ taskId: task.task_id, status: nextStatus });
                          }}
                          onSelectMatter={onSelectMatter}
                        />
                      ))}
                  </div>
                </div>
              )}

              {/* This Week */}
              {data.my_tasks.some((t) => t.bucket === "THIS_WEEK") && (
                <div>
                  <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
                    📅 This Week
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {data.my_tasks
                      .filter((t) => t.bucket === "THIS_WEEK")
                      .map((task) => (
                        <TaskCard
                          key={task.task_id}
                          task={task}
                          isDone={task.status === "DONE" || completedTaskIds.has(task.task_id)}
                          onToggle={() => {
                            const isDone = task.status === "DONE" || completedTaskIds.has(task.task_id);
                            const nextStatus = isDone ? "PENDING" : "DONE";
                            if (nextStatus === "DONE") {
                              setCompletedTaskIds((prev) => new Set(prev).add(task.task_id));
                            } else {
                              setCompletedTaskIds((prev) => {
                                const s = new Set(prev);
                                s.delete(task.task_id);
                                return s;
                              });
                            }
                            taskStatusMutation.mutate({ taskId: task.task_id, status: nextStatus });
                          }}
                          onSelectMatter={onSelectMatter}
                        />
                      ))}
                  </div>
                </div>
              )}

              {/* Undated */}
              {data.my_tasks.some((t) => t.bucket === "UNDATED") && (
                <div>
                  <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
                    📌 Undated
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {data.my_tasks
                      .filter((t) => t.bucket === "UNDATED")
                      .map((task) => (
                        <TaskCard
                          key={task.task_id}
                          task={task}
                          isDone={task.status === "DONE" || completedTaskIds.has(task.task_id)}
                          onToggle={() => {
                            const isDone = task.status === "DONE" || completedTaskIds.has(task.task_id);
                            const nextStatus = isDone ? "PENDING" : "DONE";
                            if (nextStatus === "DONE") {
                              setCompletedTaskIds((prev) => new Set(prev).add(task.task_id));
                            } else {
                              setCompletedTaskIds((prev) => {
                                const s = new Set(prev);
                                s.delete(task.task_id);
                                return s;
                              });
                            }
                            taskStatusMutation.mutate({ taskId: task.task_id, status: nextStatus });
                          }}
                          onSelectMatter={onSelectMatter}
                        />
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Section 4: Deadlines & Dates Due */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>⏱️</span> Due This Week ({data.this_week_deadlines.length})
            </h3>
          </div>

          {data.this_week_deadlines.length === 0 ? (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px dashed var(--border)",
                borderRadius: "10px",
                padding: "20px",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No deadlines due in the next 7 days.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {data.this_week_deadlines.map((d) => (
                <DeadlineCard
                  key={d.deadline_id}
                  deadline={d}
                  onSelectMatter={onSelectMatter}
                  onMarkDone={() =>
                    deadlineLifecycleMutation.mutate({
                      deadlineId: d.deadline_id,
                      lifecycle: "DONE",
                    })
                  }
                />
              ))}
            </div>
          )}
        </section>

        {/* Section 5: This Week's Hearings */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>📅</span> Next 7 Days Listings ({data.this_week_hearings.length})
            </h3>
          </div>

          {data.this_week_hearings.length === 0 ? (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px dashed var(--border)",
                borderRadius: "10px",
                padding: "20px",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "14px",
              }}
            >
              No additional hearings listed this week.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {data.this_week_hearings.map((h) => (
                <HearingCard key={h.hearing_id} hearing={h} onSelectMatter={onSelectMatter} compact />
              ))}
            </div>
          )}
        </section>

        {/* Section 6: Recent Public Orders */}
        {data.recent_orders.length > 0 && (
          <section>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>📜</span> Orders Landed in Matters ({data.recent_orders.length})
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {data.recent_orders.map((o) => (
                <OrderCard key={o.public_id} order={o} onSelectMatter={onSelectMatter} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

// ==============================================================================
// Sub-components
// ==============================================================================

const HearingCard: React.FC<{
  hearing: TodayHearingItem;
  onSelectMatter?: (id: string) => void;
  isToday?: boolean;
  compact?: boolean;
}> = ({ hearing, onSelectMatter, isToday, compact }) => {
  return (
    <div
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: isToday ? "1px solid var(--accent)" : "1px solid var(--border)",
        borderRadius: "10px",
        padding: compact ? "12px 16px" : "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          {hearing.court_no && (
            <span
              style={{
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                color: "var(--accent)",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "12px",
                fontWeight: "700",
              }}
            >
              Court {hearing.court_no}
            </span>
          )}
          {hearing.item_no && (
            <span
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.08)",
                color: "var(--text-primary)",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "12px",
                fontWeight: "600",
              }}
            >
              Item #{hearing.item_no}
            </span>
          )}
          <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            {hearing.court_or_forum || hearing.bench || "Court"}
          </span>
        </div>

        <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-muted)" }}>
          {hearing.date}
        </span>
      </div>

      <div>
        <div
          onClick={() => onSelectMatter?.(hearing.matter_id)}
          style={{
            fontSize: "15px",
            fontWeight: "600",
            color: "var(--text-primary)",
            cursor: onSelectMatter ? "pointer" : "default",
          }}
        >
          {hearing.matter_title}
        </div>
        {hearing.purpose && (
          <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>
            Purpose: <em>{hearing.purpose}</em>
          </div>
        )}
      </div>
    </div>
  );
};

const DeadlineCard: React.FC<{
  deadline: TodayDeadlineItem;
  onSelectMatter?: (id: string) => void;
  onMarkDone?: () => void;
}> = ({ deadline, onSelectMatter, onMarkDone }) => {
  return (
    <div
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: deadline.is_overdue ? "1px solid var(--danger)" : "1px solid var(--border)",
        borderRadius: "10px",
        padding: "16px 20px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "12px",
      }}
    >
      <div style={{ flex: 1, minWidth: "240px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          {deadline.is_overdue && (
            <span
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                color: "var(--danger)",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: "700",
              }}
            >
              OVERDUE
            </span>
          )}
          <span style={{ fontSize: "13px", fontWeight: "700", color: deadline.is_overdue ? "var(--danger)" : "var(--accent)" }}>
            Due: {deadline.due_on}
          </span>
        </div>

        <div
          onClick={() => onSelectMatter?.(deadline.matter_id)}
          style={{
            fontSize: "15px",
            fontWeight: "600",
            color: "var(--text-primary)",
            cursor: onSelectMatter ? "pointer" : "default",
          }}
        >
          {deadline.label}
        </div>
        <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
          {deadline.matter_title} • <span style={{ fontStyle: "italic" }}>{deadline.source_note}</span>
        </div>
      </div>

      <button
        onClick={onMarkDone}
        style={{
          padding: "8px 14px",
          borderRadius: "6px",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          color: "var(--success)",
          border: "1px solid rgba(16, 185, 129, 0.3)",
          fontSize: "12px",
          fontWeight: "600",
          cursor: "pointer",
          minHeight: "44px",
        }}
      >
        ✓ Mark Done
      </button>
    </div>
  );
};

const CandidateCard: React.FC<{
  candidate: CaseCandidateResponse;
  onConfirm: () => void;
  onDismiss: () => void;
  isConfirming: boolean;
  isDismissing: boolean;
  onSelectMatter?: (id: string) => void;
}> = ({ candidate, onConfirm, onDismiss, isConfirming, isDismissing, onSelectMatter }) => {
  const isDropped = candidate.kind === "HEARING_DROPPED";

  return (
    <div
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "8px" }}>
        <div>
          <span
            style={{
              padding: "2px 8px",
              borderRadius: "4px",
              fontSize: "11px",
              fontWeight: "700",
              backgroundColor: isDropped ? "rgba(239, 68, 68, 0.15)" : "rgba(245, 158, 11, 0.15)",
              color: isDropped ? "var(--danger)" : "#f59e0b",
            }}
          >
            {isDropped ? "DROPPED FROM REVISED CAUSE LIST" : `${candidate.kind} MATCH CANDIDATE`}
          </span>
          <div style={{ fontSize: "14px", fontWeight: "600", marginTop: "6px" }}>
            {candidate.case_number_raw}
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
            Date: {candidate.list_date || "Unknown"} • Bench: {candidate.bench || "N/A"}
            {Boolean(candidate.details?.court_no) && ` • Court ${String(candidate.details?.court_no)}`}
            {Boolean(candidate.details?.item_no) && ` • Item #${String(candidate.details?.item_no)}`}
          </div>
          {isDropped && (
            <div style={{ fontSize: "12px", color: "var(--danger)", marginTop: "4px" }}>
              This hearing was listed in an earlier revision but is missing in the latest official cause list.
            </div>
          )}
          {candidate.matter_id && onSelectMatter && (
            <div style={{ marginTop: "6px" }}>
              <button
                onClick={() => onSelectMatter(candidate.matter_id)}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  color: "var(--accent)",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                View Linked Matter →
              </button>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={onConfirm}
            disabled={isConfirming}
            style={{
              padding: "8px 14px",
              borderRadius: "6px",
              backgroundColor: "var(--success)",
              color: "#fff",
              border: "none",
              fontSize: "12px",
              fontWeight: "600",
              cursor: "pointer",
              minHeight: "44px",
            }}
          >
            {isDropped ? "Acknowledge" : "Confirm Match"}
          </button>
          <button
            onClick={onDismiss}
            disabled={isDismissing}
            style={{
              padding: "8px 14px",
              borderRadius: "6px",
              backgroundColor: "rgba(255, 255, 255, 0.06)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border)",
              fontSize: "12px",
              fontWeight: "600",
              cursor: "pointer",
              minHeight: "44px",
            }}
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};

const OrderCard: React.FC<{
  order: CourtOrderResponse;
  onSelectMatter?: (id: string) => void;
}> = ({ order, onSelectMatter }) => {
  return (
    <div
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "14px 18px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "10px",
      }}
    >
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              backgroundColor: "rgba(245, 158, 11, 0.15)",
              color: "#f59e0b",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              padding: "2px 8px",
              borderRadius: "4px",
              fontSize: "11px",
              fontWeight: "600",
            }}
          >
            Uncertified copy from official public mirror
          </span>
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            {order.decision_date || "Date unspecified"}
          </span>
        </div>
        <div style={{ fontSize: "14px", fontWeight: "600", marginTop: "4px" }}>
          Order: {order.public_id} ({order.match_key})
        </div>
      </div>

      <button
        onClick={() => onSelectMatter?.(order.matter_id)}
        style={{
          padding: "6px 12px",
          borderRadius: "6px",
          backgroundColor: "var(--bg-primary)",
          border: "1px solid var(--border)",
          color: "var(--text-primary)",
          fontSize: "12px",
          cursor: "pointer",
        }}
      >
        View in Matter →
      </button>
    </div>
  );
};

const TaskCard: React.FC<{
  task: TodayTaskItem;
  isDone: boolean;
  onToggle: () => void;
  onSelectMatter?: (id: string) => void;
}> = ({ task, isDone, onToggle, onSelectMatter }) => {
  return (
    <div
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: `1px solid ${task.is_overdue && !isDone ? "rgba(239, 68, 68, 0.4)" : "var(--border)"}`,
        borderRadius: "8px",
        padding: "12px 16px",
        display: "flex",
        alignItems: "flex-start",
        gap: "12px",
        opacity: isDone ? 0.6 : 1,
        transition: "opacity 0.2s ease",
      }}
    >
      <label
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minWidth: "44px",
          minHeight: "44px",
          margin: "-10px 0 -10px -10px",
          cursor: "pointer",
        }}
      >
        <input
          type="checkbox"
          checked={isDone}
          onChange={onToggle}
          style={{
            width: "18px",
            height: "18px",
            cursor: "pointer",
            accentColor: "var(--accent)",
          }}
        />
      </label>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "14px",
              fontWeight: "600",
              color: "var(--text-primary)",
              textDecoration: isDone ? "line-through" : "none",
            }}
          >
            {task.title}
          </span>
          {task.is_overdue && !isDone && (
            <span
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                color: "var(--danger)",
                padding: "2px 6px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: "600",
              }}
            >
              Overdue
            </span>
          )}
          {task.due_on && (
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Due: {task.due_on}
            </span>
          )}
        </div>

        {task.notes && (
          <p
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              margin: "4px 0 0 0",
              textDecoration: isDone ? "line-through" : "none",
            }}
          >
            {task.notes}
          </p>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "6px", fontSize: "12px" }}>
          <button
            onClick={() => onSelectMatter?.(task.matter_id)}
            style={{
              background: "none",
              border: "none",
              padding: 0,
              color: "var(--accent)",
              cursor: "pointer",
              fontWeight: "500",
              textDecoration: "underline",
            }}
          >
            {task.matter_title}
          </button>
          {task.assignee_name && (
            <span style={{ color: "var(--text-muted)" }}>
              • Assigned to {task.assignee_name}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
