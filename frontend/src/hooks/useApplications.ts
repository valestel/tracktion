import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  archiveApplication,
  bulkDelete,
  bulkUpdate,
  createApplication,
  deleteApplication,
  listApplications,
  unarchiveApplication,
  updateApplication,
} from "../api/applications";
import type { ApplicationCreate, ApplicationUpdate, BulkUpdate } from "../types";

interface Filters {
  status?: string;
  company_id?: number;
  include_archived?: boolean;
}

export function useApplications(filters: Filters = {}) {
  return useQuery({
    queryKey: ["applications", filters],
    queryFn: () => listApplications(filters),
  });
}

function useAppMutation<TVariables>(
  mutationFn: (vars: TVariables) => Promise<unknown>
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });
}

export const useCreateApplication = () =>
  useAppMutation((data: ApplicationCreate) => createApplication(data));

export const useUpdateApplication = () =>
  useAppMutation(({ id, data }: { id: number; data: ApplicationUpdate }) =>
    updateApplication(id, data)
  );

export const useDeleteApplication = () =>
  useAppMutation((id: number) => deleteApplication(id));

export const useArchiveApplication = () =>
  useAppMutation((id: number) => archiveApplication(id));

export const useUnarchiveApplication = () =>
  useAppMutation((id: number) => unarchiveApplication(id));

export const useBulkUpdate = () =>
  useAppMutation((data: BulkUpdate) => bulkUpdate(data));

// Bulk delete can also remove companies left without applications,
// so the companies query must be refreshed too.
export function useBulkDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ids: number[]) => bulkDelete(ids),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.invalidateQueries({ queryKey: ["companies"] });
    },
  });
}
