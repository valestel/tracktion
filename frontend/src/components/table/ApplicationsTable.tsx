import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import type { ApplicationRead } from "../../types";
import type { useSelection } from "../../hooks/useSelection";
import { StatusPicker } from "./StatusPicker";
import { Button } from "../common/Button";
import { toHref } from "../../utils/link";
import { getRecencyTint } from "../../utils/recency";

type Selection = ReturnType<typeof useSelection>;

interface ApplicationsTableProps {
  data: ApplicationRead[];
  selection: Selection;
  onRowClick: (id: number) => void;
  onArchive: (id: number) => void;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: string) => void;
  highlightRecent: boolean;
}

const col = createColumnHelper<ApplicationRead>();

export function ApplicationsTable({
  data,
  selection,
  onRowClick,
  onArchive,
  onDelete,
  onStatusChange,
  highlightRecent,
}: ApplicationsTableProps) {
  const allIds = data.map((r) => r.id);

  const columns = [
    col.display({
      id: "select",
      header: () => (
        <input
          type="checkbox"
          checked={allIds.length > 0 && allIds.every((id) => selection.isSelected(id))}
          onChange={() => selection.toggleAll(allIds)}
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          checked={selection.isSelected(row.original.id)}
          onChange={() => selection.toggle(row.original.id)}
          onClick={(e) => e.stopPropagation()}
        />
      ),
      size: 40,
    }),
    col.accessor("company_name", { header: "Company" }),
    col.accessor("company_description", {
      header: "Description",
      cell: (info) => {
        const value = info.getValue();
        return value ? (
          <div className="company-description" title={value}>
            {value}
          </div>
        ) : null;
      },
    }),
    col.accessor("job_title", { header: "Role" }),
    col.accessor("application_date", {
      header: "Applied",
      cell: (info) => new Date(info.getValue()).toLocaleDateString(),
    }),
    col.accessor("status", {
      header: "Status",
      cell: (info) => (
        <StatusPicker
          status={info.getValue()}
          onChange={(status) => onStatusChange(info.row.original.id, status)}
        />
      ),
    }),
    col.accessor("link", {
      header: "Application Link",
      cell: (info) =>
        info.getValue() ? (
          <a
            href={toHref(info.getValue()!)}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            ↗
          </a>
        ) : null,
    }),
    col.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div style={{ display: "flex", gap: 4 }} onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            title={row.original.archived_at ? "Unarchive" : "Archive"}
            onClick={() => onArchive(row.original.id)}
          >
            {row.original.archived_at ? "↩" : "⊘"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            title="Delete"
            onClick={() => {
              if (confirm("Delete this application?")) onDelete(row.original.id);
            }}
          >
            ✕
          </Button>
        </div>
      ),
    }),
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (data.length === 0) {
    return (
      <div className="empty-state">
        <p>No applications found.</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th key={header.id} style={{ width: header.getSize() }}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => {
            const isSelected = selection.isSelected(row.original.id);
            const tint = highlightRecent ? getRecencyTint(row.original) : undefined;
            return (
              <tr
                key={row.id}
                className={isSelected ? "selected" : ""}
                style={tint && !isSelected ? { backgroundColor: tint } : undefined}
                onClick={() => onRowClick(row.original.id)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
