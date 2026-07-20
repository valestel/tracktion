import { del, get, patch, post } from "./client";
import type { ApplicationCreate, ApplicationRead, ApplicationUpdate, BulkUpdate } from "../types";

interface ListParams {
  status?: string;
  company_id?: number;
  include_archived?: boolean;
  ever_status?: string[];
  ever_status_match_all?: boolean;
}

export function listApplications(params: ListParams = {}): Promise<ApplicationRead[]> {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.company_id) qs.set("company_id", String(params.company_id));
  if (params.include_archived) qs.set("include_archived", "true");
  params.ever_status?.forEach((s) => qs.append("ever_status", s));
  if (params.ever_status_match_all) qs.set("ever_status_match_all", "true");
  const query = qs.toString();
  return get<ApplicationRead[]>(`/applications${query ? `?${query}` : ""}`);
}

export const createApplication = (data: ApplicationCreate) =>
  post<ApplicationRead>("/applications", data);

export const getApplication = (id: number) =>
  get<ApplicationRead>(`/applications/${id}`);

export const updateApplication = (id: number, data: ApplicationUpdate) =>
  patch<ApplicationRead>(`/applications/${id}`, data);

export const deleteApplication = (id: number) =>
  del(`/applications/${id}`);

export const archiveApplication = (id: number) =>
  post<ApplicationRead>(`/applications/${id}/archive`);

export const unarchiveApplication = (id: number) =>
  post<ApplicationRead>(`/applications/${id}/unarchive`);

export const bulkUpdate = (data: BulkUpdate) =>
  patch<ApplicationRead[]>("/applications/bulk", data);

export const bulkDelete = (ids: number[]) =>
  post<void>("/applications/bulk-delete", { ids });
