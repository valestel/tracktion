import { useQuery } from "@tanstack/react-query";
import { listStatuses } from "../api/statuses";
import type { Status } from "../types";

export function useStatuses() {
  const query = useQuery({
    queryKey: ["statuses"],
    queryFn: listStatuses,
    staleTime: Infinity,
  });

  const statusMap = new Map<string, Status>(
    (query.data ?? []).map((s) => [s.name, s])
  );

  return { ...query, statusMap };
}
