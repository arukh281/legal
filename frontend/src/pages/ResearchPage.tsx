import React from "react";

export const ResearchPage: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "700" }}>Research Q&A</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
          Ask corporate-law questions pinned to statutory provisions and paragraph anchors.
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
        <p style={{ fontSize: "14px", marginBottom: "8px" }}>Research Q&A Module (Session S07)</p>
        <p style={{ fontSize: "12px" }}>
          Hybrid retrieval (Postgres FTS + pgvector) and Claim-level verification will be live in Phase P5.
        </p>
      </div>
    </div>
  );
};
