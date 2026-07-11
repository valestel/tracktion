import { post, postForm } from "./client";
import type { ColumnMapping, ImportCommitResponse, ImportPreviewResponse, ImportRow } from "../types";

export async function previewImport(
  file: File,
  mapping: ColumnMapping
): Promise<ImportPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("column_mapping", JSON.stringify(mapping));
  return postForm<ImportPreviewResponse>("/import/preview", formData);
}

export const commitImport = (rows: ImportRow[]) =>
  post<ImportCommitResponse>("/import/commit", rows);
