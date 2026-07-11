import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCompany, listCompanies, updateCompany } from "../api/companies";

export function useCompanies() {
  return useQuery({ queryKey: ["companies"], queryFn: listCompanies });
}

export function useCreateCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createCompany,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["companies"] }),
  });
}

export function useUpdateCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; description?: string } }) =>
      updateCompany(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["companies"] });
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}
