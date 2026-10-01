import React from "react";

export const AlertsPage: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "700" }}>Alerts & Watchlists</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
          Targeted case notifications, statutory amendments, and impact alerts.
        </p>
      </div>

      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "32px",
          textAlign: "center",
          color: "var(--text-muted)",
        }}
      >
        <p style={{ fontSize: "14px", marginBottom: "8px" }}>Alerts & Watchlists Module (Session S17)</p>
        <p style={{ fontSize: "12px" }}>
          In-place alert updates and deduplication keys will be live in Phase P10.
        </p>
      </div>
    </div>
  );
};
