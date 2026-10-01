import React from "react";

export const AuthorityPage: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "700" }}>Authority & Citator</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
          Good law verification, negative treatment detection, and appeal history tracking.
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
        <p style={{ fontSize: "14px", marginBottom: "8px" }}>Citator & Authority View (Session S09)</p>
        <p style={{ fontSize: "12px" }}>
          Bitemporal Assertion ledger and AuthorityView badges will be live in Phase P3.
        </p>
      </div>
    </div>
  );
};
