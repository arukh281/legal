import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchToday,
  updateTaskStatus,
  type TodayResponse,
  type TodayTaskItem,
} from "../api/client";
import {
  PageHeader,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  EmptyState,
} from "../components/ui";
import { formatDate } from "../utils/format";

interface TasksPageProps {
  onSelectMatter?: (matterId: string) => void;
}

export const TasksPage: React.FC<TasksPageProps> = ({ onSelectMatter }) => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"ALL" | "OPEN" | "DONE">("OPEN");

  const { data, isLoading, error } = useQuery<TodayResponse>({
    queryKey: ["today"],
    queryFn: fetchToday,
  });

  const taskStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      updateTaskStatus(taskId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
  });

  const allTasks: TodayTaskItem[] = data?.my_tasks || [];

  const filteredTasks = allTasks.filter((t) => {
    if (filter === "OPEN") return t.status !== "DONE";
    if (filter === "DONE") return t.status === "DONE";
    return true;
  });

  return (
    <div>
      <PageHeader
        title="Tasks"
        description="Assigned tasks across matters"
      />

      <div style={{ maxWidth: "160px", marginBottom: "var(--space-4)" }}>
        <Select
          value={filter}
          onChange={(e) => setFilter(e.target.value as "ALL" | "OPEN" | "DONE")}
          options={[
            { value: "OPEN", label: "Open tasks" },
            { value: "DONE", label: "Completed" },
            { value: "ALL", label: "All tasks" },
          ]}
          aria-label="Filter tasks"
        />
      </div>

      {isLoading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading tasks...</p>
      ) : error ? (
        <p style={{ color: "var(--status-overdue-text)" }}>
          Failed to load tasks: {error instanceof Error ? error.message : String(error)}
        </p>
      ) : filteredTasks.length === 0 ? (
        <EmptyState
          message={filter === "OPEN" ? "No open tasks assigned to you." : "No tasks found."}
        />
      ) : (
        <Table>
          <Thead>
            <Tr>
              <Th style={{ width: "36px" }}></Th>
              <Th>Task</Th>
              <Th>Matter</Th>
              <Th>Assignee</Th>
              <Th>Due date</Th>
              <Th>Status</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredTasks.map((t) => {
              const isDone = t.status === "DONE";
              const isOverdue = t.is_overdue;

              return (
                <Tr key={t.task_id}>
                  <Td>
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
                      aria-label={`Mark ${t.title} ${isDone ? "open" : "done"}`}
                    />
                  </Td>
                  <Td style={{ fontWeight: 500 }}>
                    <span
                      style={{
                        textDecoration: isDone ? "line-through" : "none",
                        color: isDone ? "var(--text-faint)" : "var(--text-main)",
                      }}
                    >
                      {t.title}
                    </span>
                  </Td>
                  <Td>
                    {onSelectMatter ? (
                      <button
                        type="button"
                        onClick={() => onSelectMatter(t.matter_id)}
                        style={{
                          color: "var(--accent-link)",
                          textAlign: "left",
                          cursor: "pointer",
                          fontSize: "var(--text-base)",
                        }}
                      >
                        {t.matter_title || "Matter file"}
                      </button>
                    ) : (
                      <span>{t.matter_title || "—"}</span>
                    )}
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {t.assignee_name || "—"}
                  </Td>
                  <Td style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {t.due_on ? formatDate(t.due_on) : "—"}
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
    </div>
  );
};
