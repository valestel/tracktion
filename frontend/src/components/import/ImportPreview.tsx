import type { ImportPreviewResponse, ImportRow, StatusEventDraft } from "../../types";
import { Button } from "../common/Button";

interface ImportPreviewProps {
  preview: ImportPreviewResponse;
  onConfirm: (rows: ImportRow[]) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

// Backend sends dates as ISO (YYYY-MM-DD); display them day-first.
function formatIsoDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("T")[0].split("-");
  if (!year || !month || !day) return isoDate;
  return `${day}/${month}/${year}`;
}

function formatEventDate(timestamp: string | null): string {
  if (!timestamp) return "at import";
  const d = new Date(timestamp);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function HistoryCell({ events }: { events: StatusEventDraft[] }) {
  if (events.length <= 1) {
    return <span style={{ color: "var(--text-muted)" }}>—</span>;
  }
  return (
    <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12 }}>
      {events.map((ev, i) => (
        <li key={i}>
          {formatEventDate(ev.timestamp)}: {ev.from_status ?? "—"} → {ev.to_status}
        </li>
      ))}
    </ul>
  );
}

export function ImportPreview({ preview, onConfirm, onBack, isSubmitting }: ImportPreviewProps) {
  const newRows = preview.rows.filter((r) => !r.is_duplicate);

  return (
    <div>
      {preview.errors.length > 0 && (
        <div className="error-list">
          <strong>Parse errors ({preview.errors.length})</strong>
          <ul>
            {preview.errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      {preview.warnings.length > 0 && (
        <div className="warning-list">
          <strong>Warnings ({preview.warnings.length})</strong>
          <ul>
            {preview.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
        {newRows.length} row{newRows.length !== 1 ? "s" : ""} will be imported
        {preview.duplicate_count > 0 && `, ${preview.duplicate_count} duplicate${preview.duplicate_count !== 1 ? "s" : ""} skipped`}.
      </p>

      <div className="table-container" style={{ maxHeight: 320, overflowY: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Date</th>
              <th>Status</th>
              <th>History</th>
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, i) => (
              <tr key={i} className={`import-preview-row ${row.is_duplicate ? "duplicate" : ""}`}>
                <td>{row.company_name}</td>
                <td>{row.job_title}</td>
                <td>{formatIsoDate(row.application_date)}</td>
                <td>{row.status}</td>
                <td><HistoryCell events={row.status_events} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 20 }}>
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button
          variant="primary"
          disabled={newRows.length === 0 || isSubmitting}
          onClick={() => onConfirm(preview.rows)}
        >
          {isSubmitting ? "Importing…" : `Import ${newRows.length} row${newRows.length !== 1 ? "s" : ""}`}
        </Button>
      </div>
    </div>
  );
}
