import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Layout, type NavTab } from "./components/Layout";
import { TodayPage } from "./pages/TodayPage";
import { ResearchPage } from "./pages/ResearchPage";
import { MattersPage } from "./pages/MattersPage";
import { ClientsPage } from "./pages/ClientsPage";
import { ClientDetailPage } from "./pages/ClientDetailPage";
import { MatterDetailPage } from "./pages/MatterDetailPage";
import { AuthorityPage } from "./pages/AuthorityPage";
import { AlertsPage } from "./pages/AlertsPage";
import { LoginPlaceholder } from "./pages/LoginPlaceholder";
import { fetchHealth } from "./api/client";

export const App: React.FC = () => {
  const [userEmail, setUserEmail] = useState<string | null>("partner.lawyer@firm.in");
  const [currentTab, setCurrentTab] = useState<NavTab>("clients");
  const [activeClientId, setActiveClientId] = useState<string | null>(null);
  const [activeMatterId, setActiveMatterId] = useState<string | null>(null);

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30000,
  });

  if (!userEmail) {
    return <LoginPlaceholder onLogin={(email) => setUserEmail(email)} />;
  }

  const handleTabChange = (tab: NavTab) => {
    setActiveClientId(null);
    setActiveMatterId(null);
    setCurrentTab(tab);
  };

  return (
    <Layout
      currentTab={currentTab}
      onSelectTab={handleTabChange}
      userEmail={userEmail}
      onLogout={() => setUserEmail(null)}
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
        <MattersPage
          onSelectClient={(cid) => {
            setActiveClientId(cid);
            setCurrentTab("clients");
          }}
        />
      )}
      {currentTab === "research" && <ResearchPage />}
      {currentTab === "today" && <TodayPage health={health} healthLoading={healthLoading} />}
      {currentTab === "authority" && <AuthorityPage />}
      {currentTab === "alerts" && <AlertsPage />}
    </Layout>
  );
};
