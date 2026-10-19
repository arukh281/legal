import React from "react";
import { Button } from "./Button";
import { MoreMenu, type MenuItem } from "./MoreMenu";

export interface PageHeaderProps {
  title: string;
  description?: React.ReactNode;
  onBack?: () => void;
  primaryAction?: {
    label: string;
    onClick: () => void;
    disabled?: boolean;
  };
  moreActions?: MenuItem[];
  children?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  onBack,
  primaryAction,
  moreActions,
  children,
}) => {
  return (
    <div className="page-header">
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {onBack && (
            <Button
              variant="quiet"
              size="sm"
              onClick={onBack}
              aria-label="Go back"
              style={{ padding: "4px 8px", marginRight: "2px" }}
            >
              ←
            </Button>
          )}
          <h1 className="page-title">{title}</h1>
        </div>
        {description && <div className="page-description">{description}</div>}
      </div>

      <div className="page-actions">
        {children}
        {moreActions && moreActions.length > 0 && <MoreMenu items={moreActions} />}
        {primaryAction && (
          <Button
            variant="primary"
            onClick={primaryAction.onClick}
            disabled={primaryAction.disabled}
          >
            {primaryAction.label}
          </Button>
        )}
      </div>
    </div>
  );
};
