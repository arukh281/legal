import React, { useState } from "react";
import { devLogin, type DevLoginResponse } from "../api/client";
import { Button, Input } from "../components/ui";

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
    { email: "admin@demo.law", label: "Admin", role: "Admin" },
    { email: "partner@demo.law", label: "Partner", role: "Partner" },
    { email: "associate@demo.law", label: "Associate", role: "Associate" },
  ];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "var(--bg-subtle)",
        padding: "var(--space-4)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "380px",
          backgroundColor: "var(--bg-app)",
          border: "1px solid var(--border-main)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-8)",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        <div style={{ marginBottom: "var(--space-6)" }}>
          <h1 style={{ fontSize: "var(--text-lg)", fontWeight: "600", color: "var(--text-main)" }}>
            LawyerBrain
          </h1>
          <p style={{ fontSize: "var(--text-base)", color: "var(--text-muted)", marginTop: "var(--space-1)" }}>
            Corporate legal intelligence platform
          </p>
        </div>

        {errorMsg && (
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
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <Input
            label="Firm SSO email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="e.g. partner@demo.law"
            disabled={loading}
            required
          />

          <Button type="submit" variant="primary" disabled={loading || !email.trim()}>
            {loading ? "Signing in..." : "Sign in with SSO"}
          </Button>
        </form>

        <div style={{ marginTop: "var(--space-6)", borderTop: "1px solid var(--border-main)", paddingTop: "var(--space-4)" }}>
          <div
            style={{
              fontSize: "var(--text-sm)",
              fontWeight: "500",
              color: "var(--text-muted)",
              marginBottom: "var(--space-2)",
            }}
          >
            Demo accounts
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {DEMO_ACCOUNTS.map((acc) => (
              <Button
                key={acc.email}
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  setEmail(acc.email);
                  handleLoginWithEmail(acc.email);
                }}
                disabled={loading}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  width: "100%",
                  textAlign: "left",
                }}
              >
                <span>
                  <strong>{acc.label}:</strong> {acc.email}
                </span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--text-faint)" }}>
                  {acc.role}
                </span>
              </Button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
