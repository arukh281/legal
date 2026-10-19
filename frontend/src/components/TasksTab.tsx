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
import {
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
} from "./ui";
import { formatDate } from "../utils/format";

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
      {/* Action Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "var(--space-3)",
          marginBottom: "var(--space-4)",
        }}
      >
        <div style={{ display: "flex", gap: "var(--space-1)" }}>
          {(["OPEN", "ALL", "DONE"] as const).map((mode) => (
            <Button
              key={mode}
              variant={filter === mode ? "secondary" : "quiet"}
              size="sm"
              onClick={() => setFilter(mode)}
              style={filter === mode ? { fontWeight: 600 } : undefined}
            >
              {mode === "OPEN" ? "Open" : mode === "DONE" ? "Completed" : "All"} (
              {mode === "OPEN"
                ? (tasks || []).filter((t) => t.status === "OPEN").length
                : mode === "DONE"
                ? (tasks || []).filter((t) => t.status === "DONE").length
                : (tasks || []).length}
              )
            </Button>
          ))}
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            setActionError(null);
            setShowAddModal(true);
            if (assignableMembers.length > 0 && !assignee) {
              setAssignee(assignableMembers[0].user_id);
            }
          }}
        >
          Add task
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

      {isLoading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading tasks...</p>
      ) : error ? (
        <p style={{ color: "var(--status-overdue-text)" }}>
          Failed to load tasks: {error instanceof Error ? error.message : String(error)}
        </p>
      ) : filteredTasks.length === 0 ? (
        <EmptyState
          message={filter === "OPEN" ? "No open tasks for this matter." : "No tasks found."}
          action={
            filter === "OPEN" ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setActionError(null);
                  setShowAddModal(true);
                  if (assignableMembers.length > 0 && !assignee) {
                    setAssignee(assignableMembers[0].user_id);
                  }
                }}
              >
                Add task
              </Button>
            ) : undefined
          }
        />
      ) : (
        <Table>
          <Thead>
            <Tr>
              <Th style={{ width: "36px" }}></Th>
              <Th>Task</Th>
              <Th>Assignee</Th>
              <Th>Due date</Th>
              <Th>Linked item</Th>
              <Th>Status</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredTasks.map((task) => {
              const isDone = task.status === "DONE";
              const isOverdue = task.is_overdue;

              let linkedText = "—";
              if (task.hearing_id) {
                const matchedHearing = hearings.find((h) => h.hearing_id === task.hearing_id);
                linkedText = matchedHearing ? `Hearing: ${formatDate(matchedHearing.date)}` : "Hearing linked";
              } else if (task.deadline_id) {
                const matchedDeadline = deadlines.find((d) => d.deadline_id === task.deadline_id);
                linkedText = matchedDeadline ? `Deadline: ${formatDate(matchedDeadline.due_on)}` : "Deadline linked";
              }

              return (
                <Tr key={task.task_id}>
                  <Td>
                    <input
                      type="checkbox"
                      checked={isDone}
                      onChange={() =>
                        toggleStatusMutation.mutate({
                          taskId: task.task_id,
                          newStatus: isDone ? "OPEN" : "DONE",
                        })
                      }
                      style={{ cursor: "pointer", accentColor: "var(--accent-main)" }}
                      aria-label={`Toggle task completion for ${task.title}`}
                    />
                  </Td>
                  <Td>
                    <div>
                      <div
                        style={{
                          fontWeight: 500,
                          textDecoration: isDone ? "line-through" : "none",
                          color: isDone ? "var(--text-faint)" : "var(--text-main)",
                        }}
                      >
                        {task.title}
                      </div>
                      {task.notes && (
                        <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", marginTop: "2px" }}>
                          {task.notes}
                        </div>
                      )}
                    </div>
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)" }}>
                    <Select
                      value={task.assignee}
                      onChange={(e) =>
                        reassignMutation.mutate({
                          taskId: task.task_id,
                          newAssignee: e.target.value,
                        })
                      }
                      style={{ fontSize: "var(--text-sm)", padding: "2px 6px" }}
                      aria-label={`Assignee for ${task.title}`}
                    >
                      {assignableMembers.map((m) => (
                        <option key={m.user_id} value={m.user_id}>
                          {m.display_name || m.email}
                        </option>
                      ))}
                    </Select>
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {task.due_on ? formatDate(task.due_on) : "—"}
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {linkedText}
                  </Td>
                  <Td>
                    {isDone ? (
                      <Badge variant="done">Done</Badge>
                    ) : isOverdue ? (
                      <Badge variant="overdue">Overdue</Badge>
                    ) : (
                      <Badge variant="neutral">Open</Badge>
                    )}
                  </Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      )}

      {/* Add Task Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add task"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => createTaskMutation.mutate()}
              disabled={createTaskMutation.isPending || !title.trim() || !assignee}
            >
              {createTaskMutation.isPending ? "Creating..." : "Create task"}
            </Button>
          </>
        }
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createTaskMutation.mutate();
          }}
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}
        >
          <Input
            label="Task title *"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Draft rejoinder affidavit"
            required
            autoFocus
          />

          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea
              className="textarea"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Instructions or context..."
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
            <Select
              label="Assignee *"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              required
            >
              <option value="">Select lawyer</option>
              {assignableMembers.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {m.display_name || m.email} ({m.role})
                </option>
              ))}
            </Select>

            <Input
              label="Due date"
              type="date"
              value={dueOn}
              onChange={(e) => setDueOn(e.target.value)}
            />
          </div>

          <Select
            label="Link to matter event"
            value={linkType}
            onChange={(e) => {
              const val = e.target.value as "NONE" | "HEARING" | "DEADLINE";
              setLinkType(val);
              if (val !== "HEARING") setLinkedHearingId("");
              if (val !== "DEADLINE") setLinkedDeadlineId("");
            }}
            options={[
              { value: "NONE", label: "No linked event" },
              { value: "HEARING", label: "Link to hearing" },
              { value: "DEADLINE", label: "Link to statutory deadline" },
            ]}
          />

          {linkType === "HEARING" && (
            <Select
              label="Select hearing *"
              value={linkedHearingId}
              onChange={(e) => {
                setLinkedHearingId(e.target.value);
                const h = hearings.find((x) => x.hearing_id === e.target.value);
                if (h?.date && !dueOn) {
                  setDueOn(h.date);
                }
              }}
            >
              <option value="">Select a scheduled hearing</option>
              {hearings.map((h) => (
                <option key={h.hearing_id} value={h.hearing_id}>
                  {formatDate(h.date)} {h.court_or_forum ? `• ${h.court_or_forum}` : ""}
                </option>
              ))}
            </Select>
          )}

          {linkType === "DEADLINE" && (
            <Select
              label="Select deadline *"
              value={linkedDeadlineId}
              onChange={(e) => {
                setLinkedDeadlineId(e.target.value);
                const d = deadlines.find((x) => x.deadline_id === e.target.value);
                if (d?.due_on && !dueOn) {
                  setDueOn(d.due_on);
                }
              }}
            >
              <option value="">Select a statutory deadline</option>
              {deadlines.map((d) => (
                <option key={d.deadline_id} value={d.deadline_id}>
                  {d.label} • Due {formatDate(d.due_on)}
                </option>
              ))}
            </Select>
          )}
        </form>
      </Modal>
    </div>
  );
};
