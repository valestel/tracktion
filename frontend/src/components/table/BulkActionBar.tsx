import { useState } from "react";
import { useStatuses } from "../../hooks/useStatuses";
import { useBulkDelete, useBulkUpdate } from "../../hooks/useApplications";
import type { useSelection } from "../../hooks/useSelection";
import { Button } from "../common/Button";

interface BulkActionBarProps {
  selection: ReturnType<typeof useSelection>;
}

export function BulkActionBar({ selection }: BulkActionBarProps) {
  const { data: statuses = [] } = useStatuses();
  const bulkUpdate = useBulkUpdate();
  const bulkDelete = useBulkDelete();
  const [statusDropdownOpen, setStatusDropdownOpen] = useState(false);

  if (selection.count === 0) return null;

  const ids = Array.from(selection.selectedIds);

  const handleStatusChange = (status: string) => {
    bulkUpdate.mutate({ ids, status }, { onSuccess: () => selection.clear() });
    setStatusDropdownOpen(false);
  };

  const handleArchive = () => {
    bulkUpdate.mutate({ ids, archived: true }, { onSuccess: () => selection.clear() });
  };

  const handleDelete = () => {
    const confirmed = window.confirm(
      `Delete ${selection.count} application${selection.count === 1 ? "" : "s"}? ` +
        "This also removes their status history and any companies left without applications."
    );
    if (!confirmed) return;
    bulkDelete.mutate(ids, { onSuccess: () => selection.clear() });
  };

  return (
    <div className="bulk-bar">
      <span className="count">{selection.count} selected</span>

      <div style={{ position: "relative" }}>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setStatusDropdownOpen((o) => !o)}
        >
          Change status ▾
        </Button>
        {statusDropdownOpen && (
          <div
            style={{
              position: "absolute",
              top: "100%",
              left: 0,
              marginTop: 4,
              background: "var(--surface-raised)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              zIndex: 10,
              minWidth: 160,
            }}
          >
            {statuses.map((s) => (
              <button
                key={s.id}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "8px 14px",
                  background: "transparent",
                  border: "none",
                  color: "var(--text)",
                  textAlign: "left",
                  cursor: "pointer",
                  fontSize: 13,
                }}
                onClick={() => handleStatusChange(s.name)}
              >
                {s.name}
              </button>
            ))}
          </div>
        )}
      </div>

      <Button variant="secondary" size="sm" onClick={handleArchive}>
        Archive selected
      </Button>

      <Button variant="danger" size="sm" onClick={handleDelete} disabled={bulkDelete.isPending}>
        Delete selected
      </Button>

      <Button variant="ghost" size="sm" onClick={selection.clear}>
        Clear
      </Button>
    </div>
  );
}
