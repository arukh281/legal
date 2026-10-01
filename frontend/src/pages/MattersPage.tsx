import React from "react";

export const MattersPage: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "700" }}>Matters</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
          Client matter workspaces, procedural timelines, and living strategy memos.
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
        <p style={{ fontSize: "14px", marginBottom: "8px" }}>Matter Workspace Module (Session S10)</p>
        <p style={{ fontSize: "12px" }}>
          Isolated tenant workspaces (tpl.matter) with ethical walls and MatterContext will be live in Phase P7.
        </p>
      </div>
    </div>
  );
};
