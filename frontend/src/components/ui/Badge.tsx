import React from "react";

export type BadgeVariant = "overdue" | "due-soon" | "done" | "neutral";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "neutral",
  className = "",
  children,
  ...props
}) => {
  const variantClass =
    variant === "overdue"
      ? "badge-overdue"
      : variant === "due-soon"
      ? "badge-due-soon"
      : variant === "done"
      ? "badge-done"
      : "badge-neutral";

  return (
    <span className={`badge ${variantClass} ${className}`.trim()} {...props}>
      {children}
    </span>
  );
};
