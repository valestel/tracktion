import { useStatuses } from "../../hooks/useStatuses";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { statusMap } = useStatuses();
  const color = statusMap.get(status)?.color ?? "#94a3b8";

  return (
    <span
      className="status-badge"
      style={{ backgroundColor: color }}
    >
      {status}
    </span>
  );
}
