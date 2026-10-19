import React, { useState, useRef, useEffect } from "react";
import { Button } from "./Button";

export interface MenuItem {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export interface MoreMenuProps {
  items: MenuItem[];
  label?: string;
}

export const MoreMenu: React.FC<MoreMenuProps> = ({ items, label = "More" }) => {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  if (items.length === 0) return null;

  return (
    <div className="more-menu-container" ref={containerRef}>
      <Button
        variant="secondary"
        size="sm"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-haspopup="true"
      >
        {label} ▾
      </Button>
      {open && (
        <div className="dropdown-menu">
          {items.map((item, idx) => (
            <button
              key={idx}
              type="button"
              className="dropdown-item"
              disabled={item.disabled}
              onClick={() => {
                setOpen(false);
                item.onClick();
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
