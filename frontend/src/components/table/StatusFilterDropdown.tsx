import { useEffect, useRef, useState } from "react";
import type { Status } from "../../types";

interface StatusFilterDropdownProps {
  statuses: Status[];
  selected: string[];
  onChange: (statuses: string[]) => void;
  prefix?: string;
}

export function StatusFilterDropdown({
  statuses,
  selected,
  onChange,
  prefix,
}: StatusFilterDropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  const toggleStatus = (name: string) => {
    onChange(
      selected.includes(name) ? selected.filter((s) => s !== name) : [...selected, name]
    );
  };

  const label =
    selected.length === 0
      ? "All statuses"
      : selected.length === 1
      ? selected[0]
      : `${selected.length} statuses`;

  return (
    <div className="dropdown" ref={ref}>
      <button
        type="button"
        className={`filter-tab dropdown-trigger ${selected.length > 0 ? "active" : ""}`}
        onClick={() => setOpen((o) => !o)}
      >
        {prefix ? `${prefix}: ` : ""}
        {label} ▾
      </button>
      {open && (
        <div className="dropdown-menu">
          <label className="dropdown-item">
            <input
              type="checkbox"
              checked={selected.length === 0}
              onChange={() => onChange([])}
            />
            All statuses
          </label>
          {statuses.map((s) => (
            <label key={s.id} className="dropdown-item">
              <input
                type="checkbox"
                checked={selected.includes(s.name)}
                onChange={() => toggleStatus(s.name)}
              />
              {s.name}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
