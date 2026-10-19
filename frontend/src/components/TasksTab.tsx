import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMatterTasks,
  createMatterTask,
  updateTaskStatus,
  reassignTask,
  fetchMatterMembers,
  type TaskResponse,
  type HearingResponse,
  type DeadlineResponse,
} from "../api/client";

interface TasksTabProps {
  matterId: string;
  hearings?: HearingResponse[];
  deadlines?: DeadlineResponse[];
}

export const TasksTab: React.FC<TasksTabProps> = ({
  matterId,
  hearings = [],
  deadlines = [],
}) => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"ALL" | "OPEN" | "DONE">("OPEN");
  const [showAddModal, setShowAddModal] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // New task form state
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [assignee, setAssignee] = useState("");
  const [dueOn, setDueOn] = useState("");
  const [linkType, setLinkType] = useState<"NONE" | "HEARING" | "DEADLINE">("NONE");
  const [linkedHearingId, setLinkedHearingId] = useState("");
  const [linkedDeadlineId, setLinkedDeadlineId] = useState("");

  const { data: tasks, isLoading, error } = useQuery<TaskResponse[]>({
    queryKey: ["matter_tasks", matterId],
    queryFn: () => fetchMatterTasks(matterId),
  });

  const { data: members = [] } = useQuery({
    queryKey: ["matter_members", matterId],
    queryFn: () => fetchMatterMembers(matterId),
  });

  // Assignable members: LEAD or MEMBER only (never VIEWER)
  const assignableMembers = members.filter((m) => m.role === "LEAD" || m.role === "MEMBER");

  const createTaskMutation = useMutation({
    mutationFn: () =>
      createMatterTask(matterId, {
        title: title.trim(),
        notes: notes.trim() || undefined,
        assignee,
        due_on: dueOn || undefined,
        hearing_id: linkType === "HEARING" && linkedHearingId ? linkedHearingId : undefined,
        deadline_id: linkType === "DEADLINE" && linkedDeadlineId ? linkedDeadlineId : undefined,
      }),
    onSuccess: () => {
      setShowAddModal(false);
      setTitle("");
      setNotes("");
      setAssignee("");
      setDueOn("");
      setLinkType("NONE");
      setLinkedHearingId("");
      setLinkedDeadlineId("");
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["matter_tasks", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to create task.");
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ taskId, newStatus }: { taskId: string; newStatus: string }) =>
      updateTaskStatus(taskId, newStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter_tasks", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to update task status.");
    },
  });

  const reassignMutation = useMutation({
    mutationFn: ({ taskId, newAssignee }: { taskId: string; newAssignee: string }) =>
      reassignTask(taskId, newAssignee),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matter_tasks", matterId] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : "Failed to reassign task.");
    },
  });

  const filteredTasks = (tasks || []).filter((t) => {
    if (filter === "OPEN") return t.status === "OPEN";
    if (filter === "DONE") return t.status === "DONE";
    return true;
  });

  return (
    <div>
      {/* Top action bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "20px",
        }}
      >
        <div style={{ display: "flex", gap: "8px" }}>
          {(["OPEN", "ALL", "DONE"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setFilter(mode)}
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: "600",
                border: "1px solid var(--border)",
                backgroundColor: filter === mode ? "var(--accent)" : "var(--bg-secondary)",
                color: filter === mode ? "#fff" : "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              {mode === "OPEN" ? "Pending" : mode === "DONE" ? "Completed" : "All"} (
              {mode === "OPEN"
                ? (tasks || []).filter((t) => t.status === "OPEN").length
                : mode === "DONE"
                ? (tasks || []).filter((t) => t.status === "DONE").length
                : (tasks || []).length}
              )
            </button>
          ))}
        </div>

        <button
          onClick={() => {
            setActionError(null);
            setShowAddModal(true);
            if (assignableMembers.length > 0 && !assignee) {
              setAssignee(assignableMembers[0].user_id);
            }
          }}
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
            minHeight: "40px",
          }}
        >
          <span>+</span> Add Task
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

      {/* Task list */}
      {isLoading ? (
        <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading tasks...
        </div>
      ) : error ? (
        <div style={{ padding: "20px", textAlign: "center", color: "var(--danger)" }}>
          Failed to load tasks: {error instanceof Error ? error.message : String(error)}
        </div>
      ) : filteredTasks.length === 0 ? (
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
          No {filter === "OPEN" ? "pending" : filter === "DONE" ? "completed" : ""} tasks found for this matter.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {filteredTasks.map((task) => {
            const isDone = task.status === "DONE";
            return (
              <div
                key={task.task_id}
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  border: `1px solid ${task.is_overdue && !isDone ? "rgba(239, 68, 68, 0.4)" : "var(--border)"}`,
                  borderRadius: "8px",
                  padding: "14px 18px",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "14px",
                  opacity: isDone ? 0.65 : 1,
                  transition: "all 0.2s ease",
                }}
              >
                {/* Status checkbox */}
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
                    onChange={() =>
                      toggleStatusMutation.mutate({
                        taskId: task.task_id,
                        newStatus: isDone ? "OPEN" : "DONE",
                      })
                    }
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
                      <span
                        style={{
                          fontSize: "12px",
                          color: task.is_overdue && !isDone ? "var(--danger)" : "var(--text-muted)",
                          fontWeight: task.is_overdue && !isDone ? "600" : "400",
                        }}
                      >
                        📅 Due: {task.due_on}
                      </span>
                    )}

                    {task.hearing_id && (
                      <span
                        style={{
                          fontSize: "11px",
                          backgroundColor: "rgba(59, 130, 246, 0.1)",
                          color: "var(--accent)",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        🏛️ Linked Hearing
                      </span>
                    )}

                    {task.deadline_id && (
                      <span
                        style={{
                          fontSize: "11px",
                          backgroundColor: "rgba(168, 85, 247, 0.1)",
                          color: "#a855f7",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        ⏱️ Linked Deadline
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

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                      marginTop: "8px",
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      flexWrap: "wrap",
                    }}
                  >
                    <span>
                      Assigned to:{" "}
                      <select
                        value={task.assignee}
                        onChange={(e) =>
                          reassignMutation.mutate({
                            taskId: task.task_id,
                            newAssignee: e.target.value,
                          })
                        }
                        disabled={isDone}
                        style={{
                          padding: "2px 6px",
                          borderRadius: "4px",
                          border: "1px solid var(--border)",
                          backgroundColor: "var(--bg-primary)",
                          color: "var(--text-primary)",
                          fontSize: "12px",
                          cursor: "pointer",
                        }}
                      >
                        {assignableMembers.map((m) => (
                          <option key={m.user_id} value={m.user_id}>
                            {m.display_name} ({m.role})
                          </option>
                        ))}
                      </select>
                    </span>

                    {task.done_at && (
                      <span>
                        • Completed on {new Date(task.done_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Task Modal */}
      {showAddModal && (
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
              maxWidth: "520px",
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
              <h3 style={{ fontSize: "18px", fontWeight: "700", margin: 0 }}>Create Task</h3>
              <button
                onClick={() => setShowAddModal(false)}
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

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createTaskMutation.mutate();
              }}
              style={{ display: "flex", flexDirection: "column", gap: "14px" }}
            >
              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Task Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Draft Rejoinder Affidavit"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
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
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Assignee * (LEAD or MEMBER)
                </label>
                <select
                  required
                  value={assignee}
                  onChange={(e) => setAssignee(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                  }}
                >
                  <option value="">Select Assignee</option>
                  {assignableMembers.map((m) => (
                    <option key={m.user_id} value={m.user_id}>
                      {m.display_name} ({m.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Due Date (Optional)
                </label>
                <input
                  type="date"
                  value={dueOn}
                  onChange={(e) => setDueOn(e.target.value)}
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
              </div>

              <div>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Notes (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Additional context or filing checklist items..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-primary)",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                    resize: "vertical",
                  }}
                />
              </div>

              {/* Link mutually exclusive: Hearing OR Deadline */}
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
                <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "6px" }}>
                  Link to Hearing or Deadline (Optional)
                </label>
                <div style={{ display: "flex", gap: "16px", marginBottom: "8px", fontSize: "13px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="linkType"
                      checked={linkType === "NONE"}
                      onChange={() => {
                        setLinkType("NONE");
                        setLinkedHearingId("");
                        setLinkedDeadlineId("");
                      }}
                    />
                    None
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="linkType"
                      checked={linkType === "HEARING"}
                      onChange={() => {
                        setLinkType("HEARING");
                        setLinkedDeadlineId("");
                      }}
                    />
                    Hearing
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="linkType"
                      checked={linkType === "DEADLINE"}
                      onChange={() => {
                        setLinkType("DEADLINE");
                        setLinkedHearingId("");
                      }}
                    />
                    Deadline
                  </label>
                </div>

                {linkType === "HEARING" && (
                  <select
                    value={linkedHearingId}
                    onChange={(e) => setLinkedHearingId(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 10px",
                      borderRadius: "6px",
                      border: "1px solid var(--border)",
                      backgroundColor: "var(--bg-primary)",
                      color: "var(--text-primary)",
                      fontSize: "13px",
                    }}
                  >
                    <option value="">Select linked hearing</option>
                    {hearings.map((h) => (
                      <option key={h.hearing_id} value={h.hearing_id}>
                        {h.date} - {h.purpose || "Listing"} ({h.court_no || "Court"})
                      </option>
                    ))}
                  </select>
                )}

                {linkType === "DEADLINE" && (
                  <select
                    value={linkedDeadlineId}
                    onChange={(e) => setLinkedDeadlineId(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 10px",
                      borderRadius: "6px",
                      border: "1px solid var(--border)",
                      backgroundColor: "var(--bg-primary)",
                      color: "var(--text-primary)",
                      fontSize: "13px",
                    }}
                  >
                    <option value="">Select linked deadline</option>
                    {deadlines.map((d) => (
                      <option key={d.deadline_id} value={d.deadline_id}>
                        {d.due_on} - {d.label}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
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
                  disabled={createTaskMutation.isPending || !title.trim() || !assignee}
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
                  {createTaskMutation.isPending ? "Creating..." : "Create Task"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
