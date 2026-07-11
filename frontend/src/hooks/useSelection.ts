import { useState } from "react";

export function useSelection() {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const toggle = (id: number) =>
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const toggleAll = (ids: number[]) =>
    setSelectedIds((prev) => {
      const allSelected = ids.every((id) => prev.has(id));
      return allSelected ? new Set() : new Set(ids);
    });

  const clear = () => setSelectedIds(new Set());

  const isSelected = (id: number) => selectedIds.has(id);

  return { selectedIds, toggle, toggleAll, clear, isSelected, count: selectedIds.size };
}
