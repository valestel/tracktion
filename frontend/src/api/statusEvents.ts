import { del, patch, post } from "./client";
import type { StatusEventRead } from "../types";

export interface StatusEventCreate {
  to_status: string;
  timestamp: string;
}

export interface StatusEventUpdate {
  to_status?: string;
  timestamp?: string;
}

export const createStatusEvent = (applicationId: number, data: StatusEventCreate) =>
  post<StatusEventRead>(`/applications/${applicationId}/events`, data);

export const updateStatusEvent = (eventId: number, data: StatusEventUpdate) =>
  patch<StatusEventRead>(`/events/${eventId}`, data);

export const deleteStatusEvent = (eventId: number) => del(`/events/${eventId}`);
