import { useState } from "react";
import type { ColumnMapping } from "../../types";
import { Button } from "../common/Button";

const REQUIRED_FIELDS: (keyof ColumnMapping)[] = [
  "company_name",
  "job_title",
  "application_date",
  "status",
];
const OPTIONAL_FIELDS: (keyof ColumnMapping)[] = ["company_description", "link", "notes"];
const ALL_FIELDS = [...REQUIRED_FIELDS, ...OPTIONAL_FIELDS];

const FIELD_LABELS: Record<keyof ColumnMapping, string> = {
  company_name: "Company name",
  company_description: "Company description",
  job_title: "Job title",
  application_date: "Application date",
  status: "Status",
  link: "Link / Email",
  notes: "Notes",
};

// Common header spellings that should auto-map to each field.
const FIELD_ALIASES: Record<keyof ColumnMapping, string[]> = {
  company_name: ["company"],
  company_description: ["description", "company_description"],
  job_title: ["role", "title", "position"],
  application_date: ["date", "applied_on"],
  status: [],
  link: ["link", "url", "mail", "email"],
  notes: ["notes", "note", "log"],
};

function normalizeHeader(header: string): string {
  // strip a leading UTF-8 BOM before matching
  return header.toLowerCase().replace(/^\uFEFF/, "").replace(/[\s_-]+/g, "_");
}

function autoMap(csvHeaders: string[]): Partial<ColumnMapping> {
  const auto: Partial<ColumnMapping> = {};
  const used = new Set<string>();

  // Pass 1: exact match on field name or alias
  for (const field of ALL_FIELDS) {
    const match = csvHeaders.find((h) => {
      const n = normalizeHeader(h);
      return !used.has(h) && (n === field || FIELD_ALIASES[field].includes(n));
    });
    if (match) {
      auto[field] = match;
      used.add(match);
    }
  }

  // Pass 2: for still-unmapped fields, accept a header that contains an alias
  // (e.g. "application link/mail" → link, "status log/notes" → notes)
  for (const field of ALL_FIELDS) {
    if (auto[field]) continue;
    const match = csvHeaders.find((h) => {
      const n = normalizeHeader(h);
      return !used.has(h) && FIELD_ALIASES[field].some((a) => n.includes(a));
    });
    if (match) {
      auto[field] = match;
      used.add(match);
    }
  }

  return auto;
}

interface ColumnMapperProps {
  csvHeaders: string[];
  onNext: (mapping: ColumnMapping) => void;
  onBack: () => void;
}

export function ColumnMapper({ csvHeaders, onNext, onBack }: ColumnMapperProps) {
  const [mapping, setMapping] = useState<ColumnMapping>(() => autoMap(csvHeaders));

  const requiredMapped = REQUIRED_FIELDS.every((f) => mapping[f]);

  const set = (field: keyof ColumnMapping, value: string) =>
    setMapping((prev) => ({ ...prev, [field]: value || undefined }));

  return (
    <div>
      <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>
        Match your CSV columns to the application fields.
      </p>

      <div className="column-mapper-grid">
        {ALL_FIELDS.map((field) => (
          <>
            <div
              key={`label-${field}`}
              className={`field-label ${REQUIRED_FIELDS.includes(field) ? "required" : ""}`}
            >
              {FIELD_LABELS[field]}
            </div>
            <div key={`select-${field}`} className="form-group" style={{ margin: 0 }}>
              <select
                value={mapping[field] ?? ""}
                onChange={(e) => set(field, e.target.value)}
              >
                <option value="">— skip —</option>
                {csvHeaders.map((h) => (
                  <option key={h} value={h}>
                    {h}
                  </option>
                ))}
              </select>
            </div>
          </>
        ))}
      </div>

      <div
        style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}
      >
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button variant="primary" disabled={!requiredMapped} onClick={() => onNext(mapping)}>
          Preview import
        </Button>
      </div>
    </div>
  );
}
