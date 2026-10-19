import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Layout, type NavTab } from "./components/Layout";
import { TodayPage } from "./pages/TodayPage";
import { ResearchPage } from "./pages/ResearchPage";
import { MattersPage } from "./pages/MattersPage";
import { ClientsPage } from "./pages/ClientsPage";
import { ClientDetailPage } from "./pages/ClientDetailPage";
import { MatterDetailPage } from "./pages/MatterDetailPage";
import { TasksPage } from "./pages/TasksPage";
import { ImportCasesPage } from "./pages/ImportCasesPage";
import { AuthorityPage } from "./pages/AuthorityPage";
import { AlertsPage } from "./pages/AlertsPage";
import { LoginPlaceholder } from "./pages/LoginPlaceholder";
import { logout, type DevLoginResponse } from "./api/client";

export const App: React.FC = () => {
  const queryClient = useQueryClient();
  const [currentUser, setCurrentUser] = useState<DevLoginResponse | null>(null);
  const [currentTab, setCurrentTab] = useState<NavTab>("today");
  const [activeClientId, setActiveClientId] = useState<string | null>(null);
  const [activeMatterId, setActiveMatterId] = useState<string | null>(null);

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // session termination fallback
    }
    setCurrentUser(null);
    queryClient.clear();
  };

  if (!currentUser) {
    return <LoginPlaceholder onLogin={(user) => setCurrentUser(user)} />;
  }

  const handleTabChange = (tab: NavTab) => {
    setActiveClientId(null);
    setActiveMatterId(null);
    setCurrentTab(tab);
  };

  const handleSelectMatter = (matterId: string) => {
    setActiveMatterId(matterId);
    setCurrentTab("matters");
  };

  return (
    <Layout
      currentTab={currentTab}
      onSelectTab={handleTabChange}
      userEmail={currentUser.email}
      userRole={currentUser.role}
      onLogout={handleLogout}
    >
      {currentTab === "clients" && (
        activeMatterId ? (
          <MatterDetailPage
            matterId={activeMatterId}
            onBack={() => setActiveMatterId(null)}
            onSelectClient={(cid) => {
              setActiveClientId(cid);
              setActiveMatterId(null);
            }}
          />
        ) : activeClientId ? (
          <ClientDetailPage
            clientId={activeClientId}
            onBack={() => setActiveClientId(null)}
            onSelectMatter={(mid) => setActiveMatterId(mid)}
          />
        ) : (
          <ClientsPage onSelectClient={(cid) => setActiveClientId(cid)} />
        )
      )}

      {currentTab === "matters" && (
        activeMatterId ? (
          <MatterDetailPage
            matterId={activeMatterId}
            onBack={() => setActiveMatterId(null)}
            onSelectClient={(cid) => {
              setActiveClientId(cid);
              setActiveMatterId(null);
            }}
          />
        ) : (
          <MattersPage
            onSelectClient={(cid) => {
              setActiveClientId(cid);
              setCurrentTab("clients");
            }}
          />
        )
      )}

      {currentTab === "today" && (
        <TodayPage onSelectMatter={handleSelectMatter} />
      )}

      {currentTab === "tasks" && (
        <TasksPage onSelectMatter={handleSelectMatter} />
      )}

      {currentTab === "import" && (
        <ImportCasesPage
          onBack={() => setCurrentTab("matters")}
          onViewMatters={() => setCurrentTab("matters")}
        />
      )}

      {currentTab === "research" && <ResearchPage />}
      {currentTab === "authority" && <AuthorityPage />}
      {currentTab === "alerts" && <AlertsPage />}
    </Layout>
  );
};
