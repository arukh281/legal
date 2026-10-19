import React from "react";
import type { HealthResponse } from "../api/client";

export type NavTab = "clients" | "matters" | "research" | "today" | "authority" | "alerts";

interface LayoutProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
  userEmail?: string;
  onLogout?: () => void;
  health?: HealthResponse;
  healthLoading?: boolean;
}

export const Layout: React.FC<LayoutProps> = ({
  currentTab,
  onSelectTab,
  children,
  userEmail,
  onLogout,
  health,
  healthLoading,
}) => {
  const navItems: { id: NavTab; label: string; icon: string }[] = [
    { id: "today", label: "Today", icon: "☀️" },
    { id: "clients", label: "Clients", icon: "🏢" },
    { id: "matters", label: "Matters", icon: "📁" },
    { id: "research", label: "Research", icon: "🔍" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar Navigation */}
      <aside
        style={{
          width: "240px",
          backgroundColor: "var(--bg-secondary)",
          borderRight: "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          padding: "20px 16px",
        }}
      >
        <div style={{ marginBottom: "28px", paddingLeft: "8px" }}>
          <h1 style={{ fontSize: "18px", fontWeight: "700", letterSpacing: "-0.02em" }}>
            Lawyer<span style={{ color: "var(--accent)" }}>Brain</span>
          </h1>
          <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
            Corporate Legal Intelligence
          </p>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
          {navItems.map((item) => {
            const active = currentTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-item-${item.id}`}
                onClick={() => onSelectTab(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  fontSize: "14px",
                  fontWeight: active ? "600" : "500",
                  color: active ? "#ffffff" : "var(--text-secondary)",
                  backgroundColor: active ? "var(--accent)" : "transparent",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User / Session Footer & Health */}
        <div
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: "16px",
            fontSize: "12px",
            color: "var(--text-muted)",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          {/* Compact Platform Health Pill */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "6px 10px",
              backgroundColor: "rgba(255, 255, 255, 0.03)",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              fontSize: "11px",
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "7px",
                  height: "7px",
                  borderRadius: "50%",
                  backgroundColor: health?.status === "ok" ? "var(--success)" : "var(--warning)",
                  display: "inline-block",
                }}
              />
              System
            </span>
            <span style={{ color: "var(--text-muted)", fontWeight: "500" }}>
              {healthLoading ? "..." : health?.database ? "Postgres 18" : "Online"}
            </span>
          </div>

          {userEmail ? (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                {userEmail}
              </span>
              {onLogout && (
                <button
                  onClick={onLogout}
                  style={{ color: "var(--danger)", fontSize: "11px", fontWeight: "600" }}
                >
                  Logout
                </button>
              )}
            </div>
          ) : (
            <span>Signed in as Partner Associate</span>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: "32px 40px", overflowY: "auto" }}>
        {children}
      </main>
    </div>
  );
};
