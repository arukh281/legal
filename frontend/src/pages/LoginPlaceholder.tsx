import React, { useState } from "react";
import { devLogin, type DevLoginResponse } from "../api/client";

interface LoginPlaceholderProps {
  onLogin: (user: DevLoginResponse) => void;
}

export const LoginPlaceholder: React.FC<LoginPlaceholderProps> = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLoginWithEmail = async (targetEmail: string) => {
    if (!targetEmail.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const user = await devLogin(targetEmail.trim());
      onLogin(user);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to sign in.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLoginWithEmail(email);
  };

  const DEMO_ACCOUNTS = [
    { email: "admin@demo.law", label: "Admin", role: "ADMIN" },
    { email: "partner@demo.law", label: "Partner", role: "PARTNER" },
    { email: "associate@demo.law", label: "Associate", role: "ASSOCIATE" },
  ];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "var(--bg-primary)",
        padding: "20px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "32px",
          boxShadow: "0 8px 24px rgba(0, 0, 0, 0.2)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <h1 style={{ fontSize: "24px", fontWeight: "700", letterSpacing: "-0.02em", margin: 0 }}>
            Lawyer<span style={{ color: "var(--accent)" }}>Brain</span>
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
            Corporate Legal Intelligence Platform
          </p>
        </div>

        {errorMsg && (
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
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px" }}>
              Firm SSO Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. partner@demo.law"
              disabled={loading}
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
            disabled={loading || !email.trim()}
            style={{
              padding: "10px",
              borderRadius: "6px",
              backgroundColor: loading ? "var(--border)" : "var(--accent)",
              color: "#ffffff",
              fontSize: "14px",
              fontWeight: "600",
              cursor: loading ? "not-allowed" : "pointer",
              border: "none",
            }}
          >
            {loading ? "Signing in..." : "Sign In with SSO"}
          </button>
        </form>

        <div style={{ marginTop: "24px", borderTop: "1px solid var(--border)", paddingTop: "20px" }}>
          <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "10px", textAlign: "center" }}>
            Demo Accounts (Demo Law Chambers)
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                onClick={() => {
                  setEmail(acc.email);
                  handleLoginWithEmail(acc.email);
                }}
                disabled={loading}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                  fontSize: "12px",
                  cursor: loading ? "not-allowed" : "pointer",
                  textAlign: "left",
                }}
              >
                <span>
                  <strong>{acc.label}:</strong> {acc.email}
                </span>
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: "700",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    backgroundColor: "rgba(99, 102, 241, 0.15)",
                    color: "var(--accent)",
                  }}
                >
                  {acc.role}
                </span>
              </button>
            ))}
          </div>
        </div>

        <p style={{ fontSize: "11px", color: "var(--text-muted)", textAlign: "center", marginTop: "20px", marginBottom: 0 }}>
          Local development authentication with multi-firm isolation.
        </p>
      </div>
    </div>
  );
};
