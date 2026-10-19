import React from "react";

export interface TabItem<T extends string = string> {
  id: T;
  label: string;
  count?: number;
}

export interface TabsProps<T extends string = string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onTabChange: (id: T) => void;
  className?: string;
}

export const Tabs = <T extends string>({
  tabs,
  activeTab,
  onTabChange,
  className = "",
}: TabsProps<T>): React.ReactElement => {
  return (
    <div className={`tabs ${className}`.trim()}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            className={`tab-btn ${isActive ? "active" : ""}`.trim()}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
            {typeof tab.count === "number" && (
              <span style={{ marginLeft: "6px", opacity: 0.7, fontSize: "12px" }}>
                ({tab.count})
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
