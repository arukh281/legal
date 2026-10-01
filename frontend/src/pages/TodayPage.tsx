import React from "react";
import type { HealthResponse } from "../api/client";

interface TodayPageProps {
  health?: HealthResponse | null;
  healthLoading?: boolean;
}

export const TodayPage: React.FC<TodayPageProps> = ({ health, healthLoading }) => {
  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "700" }}>Today</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
          Daily priority summary, upcoming court deadlines, and digest items.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px" }}>
        {/* System Health Status Card */}
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            padding: "20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "14px", fontWeight: "600" }}>Platform Status</span>
            <span
              style={{
                display: "inline-block",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "12px",
                fontWeight: "600",
                backgroundColor: health?.status === "ok" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                color: health?.status === "ok" ? "var(--success)" : "var(--warning)",
              }}
            >
              {healthLoading ? "Checking..." : (health?.status || "Unknown").toUpperCase()}
            </span>
          </div>

          <div style={{ fontSize: "13px", color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: "8px" }}>
            <div>Database: <strong style={{ color: "var(--text-primary)" }}>{health?.database || "Checking..."}</strong></div>
            <div>Schemas: <strong style={{ color: "var(--text-primary)" }}>{health?.schemas?.join(", ") || "None"}</strong></div>
            <div>Checked at: <span style={{ color: "var(--text-muted)" }}>{health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "..."}</span></div>
          </div>
        </div>

        {/* Priority Deadlines Card */}
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            padding: "20px",
          }}
        >
          <span style={{ fontSize: "14px", fontWeight: "600", display: "block", marginBottom: "12px" }}>
            Upcoming Deadlines (Procedural Clock)
          </span>
          <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            No pending matter deadlines for today. RuleSpec engine will populate active triggers.
          </p>
        </div>
      </div>
    </div>
  );
};
