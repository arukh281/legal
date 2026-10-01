import React from "react";

export type NavTab = "today" | "research" | "matters" | "authority" | "alerts";

interface LayoutProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
  userEmail?: string;
  onLogout?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  currentTab,
  onSelectTab,
  children,
  userEmail,
  onLogout,
}) => {
  const navItems: { id: NavTab; label: string; icon: string }[] = [
    { id: "today", label: "Today", icon: "☀️" },
    { id: "research", label: "Research", icon: "🔍" },
    { id: "matters", label: "Matters", icon: "📁" },
    { id: "authority", label: "Authority", icon: "⚖️" },
    { id: "alerts", label: "Alerts", icon: "🔔" },
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

        {/* User / Session Footer */}
        <div
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: "16px",
            fontSize: "12px",
            color: "var(--text-muted)",
          }}
        >
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
