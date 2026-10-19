import React from "react";
import { Button } from "./ui";

export type NavTab =
  | "today"
  | "clients"
  | "matters"
  | "tasks"
  | "import"
  | "research"
  | "authority"
  | "alerts";

interface LayoutProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
  userEmail?: string;
  userRole?: string;
  onLogout?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  currentTab,
  onSelectTab,
  children,
  userEmail,
  userRole,
  onLogout,
}) => {
  const isAdmin = userRole === "ADMIN";

  const navItems: { id: NavTab; label: string }[] = [
    { id: "today", label: "Today" },
    { id: "clients", label: "Clients" },
    { id: "matters", label: "Matters" },
    { id: "tasks", label: "Tasks" },
    ...(isAdmin ? [{ id: "import" as NavTab, label: "Import" }] : []),
  ];

  return (
    <div className="app-container">
      {/* Slim Left Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">LawyerBrain</div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const active = currentTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-item-${item.id}`}
                onClick={() => onSelectTab(item.id)}
                className={`sidebar-item ${active ? "active" : ""}`.trim()}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Footer: User Name and Sign out */}
        <div className="sidebar-footer">
          <div className="sidebar-user" title={userEmail || "Signed in"}>
            {userEmail || "Signed in"}
          </div>
          {onLogout && (
            <Button
              variant="quiet"
              size="sm"
              onClick={onLogout}
              style={{ justifyContent: "flex-start", padding: "4px 0", color: "var(--text-faint)" }}
            >
              Sign out
            </Button>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="page-wrapper">{children}</div>
      </main>
    </div>
  );
};
