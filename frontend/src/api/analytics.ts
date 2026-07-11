import { get } from "./client";
import type { FunnelData, SankeyData, StatusEventRead } from "../types";

export const getSankey = () => get<SankeyData>("/analytics/sankey");
export const getFunnel = () => get<FunnelData>("/analytics/funnel");
export const getTimeline = (applicationId: number) =>
  get<StatusEventRead[]>(`/analytics/timeline/${applicationId}`);
