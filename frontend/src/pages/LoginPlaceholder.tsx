import React, { useState } from "react";

interface LoginPlaceholderProps {
  onLogin: (email: string) => void;
}

export const LoginPlaceholder: React.FC<LoginPlaceholderProps> = ({ onLogin }) => {
  const [email, setEmail] = useState("associate@partnerlaw.in");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      onLogin(email.trim());
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "var(--bg-primary)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "32px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <h1 style={{ fontSize: "22px", fontWeight: "700" }}>
            Lawyer<span style={{ color: "var(--accent)" }}>Brain</span>
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
            Corporate Legal Intelligence Platform
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px" }}>
              Firm SSO Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="lawyer@firm.in"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "6px",
                border: "1px solid var(--border)",
                backgroundColor: "var(--bg-primary)",
                color: "var(--text-primary)",
                fontSize: "14px",
              }}
              required
            />
          </div>

          <button
            type="submit"
            style={{
              padding: "10px",
              borderRadius: "6px",
              backgroundColor: "var(--accent)",
              color: "#ffffff",
              fontSize: "14px",
              fontWeight: "600",
              marginTop: "8px",
            }}
          >
            Sign In with Firm SSO (Placeholder)
          </button>
        </form>

        <p style={{ fontSize: "11px", color: "var(--text-muted)", textAlign: "center", marginTop: "20px" }}>
          django-allauth SSO (Google / Microsoft Entra) will be connected in Session S03.
        </p>
      </div>
    </div>
  );
};
