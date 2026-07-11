import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useStatuses } from "../../hooks/useStatuses";
import { StatusBadge } from "./StatusBadge";

interface StatusPickerProps {
  status: string;
  onChange: (status: string) => void;
}

export function StatusPicker({ status, onChange }: StatusPickerProps) {
  const { data: statuses = [] } = useStatuses();
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const close = () => setOpen(false);

    const onClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        !triggerRef.current?.contains(target) &&
        !menuRef.current?.contains(target)
      ) {
        close();
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    const onScroll = (e: Event) => {
      // Scrolling inside the menu's own list (long status lists) shouldn't close it —
      // only scrolling the page/table behind it should.
      if (menuRef.current?.contains(e.target as Node)) return;
      close();
    };

    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [open]);

  const handleTriggerClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const rect = triggerRef.current?.getBoundingClientRect();
    if (rect) setPosition({ top: rect.bottom + 6, left: rect.left });
    setOpen((o) => !o);
  };

  const selectStatus = (name: string) => {
    if (name !== status) onChange(name);
    setOpen(false);
  };

  return (
    <>
      <button
        type="button"
        ref={triggerRef}
        className="status-picker-trigger"
        onClick={handleTriggerClick}
      >
        <StatusBadge status={status} />
      </button>
      {open &&
        position &&
        createPortal(
          <div
            ref={menuRef}
            className="dropdown-menu"
            style={{ position: "fixed", top: position.top, left: position.left }}
          >
            {statuses.map((s) => (
              <div
                key={s.id}
                className="dropdown-item"
                onMouseDown={() => selectStatus(s.name)}
              >
                <StatusBadge status={s.name} />
              </div>
            ))}
          </div>,
          document.body
        )}
    </>
  );
}
