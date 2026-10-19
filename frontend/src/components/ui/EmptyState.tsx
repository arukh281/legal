import React from "react";

export interface EmptyStateProps {
  message: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  message,
  action,
  className = "",
}) => {
  return (
    <div className={`empty-state ${className}`.trim()}>
      <p>{message}</p>
      {action && <div style={{ marginTop: "12px" }}>{action}</div>}
    </div>
  );
};
