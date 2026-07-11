import { get, patch, post } from "./client";
import type { Company } from "../types";

export const listCompanies = () => get<Company[]>("/companies");

export const createCompany = (data: { name: string; description?: string }) =>
  post<Company>("/companies", data);

export const updateCompany = (id: number, data: { name?: string; description?: string }) =>
  patch<Company>(`/companies/${id}`, data);
