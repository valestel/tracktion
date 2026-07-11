export interface Company {
  id: number;
  name: string;
  description: string | null;
}

export interface ApplicationRead {
  id: number;
  company_id: number;
  company_name: string;
  company_description: string | null;
  job_title: string;
  application_date: string;
  link: string | null;
  status: string;
  notes: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  last_status_change_at: string | null;
}

export interface ApplicationCreate {
  company_id: number;
  job_title: string;
  application_date: string;
  link?: string;
  status: string;
  notes?: string;
}

export interface ApplicationUpdate {
  company_id?: number;
  job_title?: string;
  application_date?: string;
  link?: string;
  status?: string;
  notes?: string;
}

export interface BulkUpdate {
  ids: number[];
  status?: string;
  archived?: boolean;
}

export interface Status {
  id: number;
  name: string;
  color: string | null;
  sort_order: number;
}

export interface StatusEventRead {
  id: number;
  application_id: number;
  from_status: string | null;
  to_status: string;
  timestamp: string;
  note: string | null;
}

export interface SankeyData {
  nodes: { id: string; name: string }[];
  links: { source: string; target: string; value: number }[];
}

export interface FunnelData {
  stages: { name: string; count: number }[];
}

export interface ColumnMapping {
  company_name?: string;
  company_description?: string;
  job_title?: string;
  application_date?: string;
  link?: string;
  status?: string;
  notes?: string;
}

export interface StatusEventDraft {
  from_status: string | null;
  to_status: string;
  timestamp: string | null;
}

export interface ImportRow {
  company_name: string;
  company_description?: string;
  job_title: string;
  application_date: string;
  link?: string;
  status: string;
  notes?: string;
  is_duplicate: boolean;
  status_events: StatusEventDraft[];
}

export interface ImportPreviewResponse {
  rows: ImportRow[];
  errors: string[];
  warnings: string[];
  duplicate_count: number;
}

export interface ImportCommitResponse {
  created: number;
  skipped: number;
}
