import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "quiet" | "danger";
  size?: "sm" | "base";
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = "secondary",
  size = "base",
  className = "",
  disabled,
  children,
  ...props
}) => {
  const variantClass =
    variant === "primary"
      ? "btn-primary"
      : variant === "quiet"
      ? "btn-quiet"
      : variant === "danger"
      ? "btn-danger"
      : "btn-secondary";

  const sizeClass = size === "sm" ? "btn-sm" : "";

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${className}`.trim()}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
