import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Layout, type NavTab } from "./components/Layout";
import { TodayPage } from "./pages/TodayPage";
import { ResearchPage } from "./pages/ResearchPage";
import { MattersPage } from "./pages/MattersPage";
import { AuthorityPage } from "./pages/AuthorityPage";
import { AlertsPage } from "./pages/AlertsPage";
import { LoginPlaceholder } from "./pages/LoginPlaceholder";
import { fetchHealth } from "./api/client";

export const App: React.FC = () => {
  const [userEmail, setUserEmail] = useState<string | null>("partner.lawyer@firm.in");
  const [currentTab, setCurrentTab] = useState<NavTab>("today");

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30000,
  });

  if (!userEmail) {
    return <LoginPlaceholder onLogin={(email) => setUserEmail(email)} />;
  }

  return (
    <Layout
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      userEmail={userEmail}
      onLogout={() => setUserEmail(null)}
    >
      {currentTab === "today" && <TodayPage health={health} healthLoading={healthLoading} />}
      {currentTab === "research" && <ResearchPage />}
      {currentTab === "matters" && <MattersPage />}
      {currentTab === "authority" && <AuthorityPage />}
      {currentTab === "alerts" && <AlertsPage />}
    </Layout>
  );
};
