import { useEffect, useState } from "react";
import { useApplications, useArchiveApplication, useCreateApplication, useDeleteApplication, useUpdateApplication } from "../hooks/useApplications";
import { useStatuses } from "../hooks/useStatuses";
import { useSelection } from "../hooks/useSelection";
import { ApplicationsTable } from "../components/table/ApplicationsTable";
import { StatusFilterDropdown } from "../components/table/StatusFilterDropdown";
import { BulkActionBar } from "../components/table/BulkActionBar";
import { ApplicationDetail } from "../components/detail/ApplicationDetail";
import { ApplicationForm } from "../components/detail/ApplicationForm";
import { ImportWizard } from "../components/import/ImportWizard";
import { Modal } from "../components/common/Modal";
import { Button } from "../components/common/Button";
import { Toggle } from "../components/common/Toggle";
import type { ApplicationRead } from "../types";

export function ApplicationsPage() {
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [everStatuses, setEverStatuses] = useState<string[]>([]);
  const [matchAllEverStatuses, setMatchAllEverStatuses] = useState(false);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [highlightRecent, setHighlightRecent] = useState<boolean>(
    () => localStorage.getItem("highlightRecent") !== "false"
  );

  useEffect(() => {
    localStorage.setItem("highlightRecent", String(highlightRecent));
  }, [highlightRecent]);
  const [selectedApp, setSelectedApp] = useState<ApplicationRead | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [showImport, setShowImport] = useState(false);

  const { data: statuses = [] } = useStatuses();
  const selection = useSelection();

  const { data: fetchedApplications = [], isLoading } = useApplications({
    include_archived: includeArchived,
    ever_status: everStatuses,
    ever_status_match_all: matchAllEverStatuses,
  });

  const applications =
    selectedStatuses.length === 0
      ? fetchedApplications
      : fetchedApplications.filter((a) => selectedStatuses.includes(a.status));

  const createApp = useCreateApplication();
  const archive = useArchiveApplication();
  const del = useDeleteApplication();
  const update = useUpdateApplication();

  // When filter changes, sync selectedApp if it's no longer in the list
  const visibleIds = new Set(applications.map((a) => a.id));
  const currentApp =
    selectedApp && visibleIds.has(selectedApp.id)
      ? applications.find((a) => a.id === selectedApp.id) ?? selectedApp
      : selectedApp;

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="page-header">
        <h1>Applications</h1>
        <div className="page-actions">
          <Button variant="primary" size="md" onClick={() => setShowNewForm(true)}>
            + New
          </Button>
          <Button variant="secondary" size="md" onClick={() => setShowImport(true)}>
            Import CSV
          </Button>
        </div>
      </div>

      <div className="filter-tabs">
        <StatusFilterDropdown
          statuses={statuses}
          selected={selectedStatuses}
          onChange={(next) => {
            setSelectedStatuses(next);
            selection.clear();
          }}
        />
        <StatusFilterDropdown
          statuses={statuses}
          selected={everStatuses}
          onChange={(next) => {
            setEverStatuses(next);
            selection.clear();
          }}
          prefix="Ever had"
        />
        {everStatuses.length > 1 && (
          <Toggle
            checked={matchAllEverStatuses}
            onChange={setMatchAllEverStatuses}
            label="Match all selected"
          />
        )}
        <Toggle
          checked={highlightRecent}
          onChange={setHighlightRecent}
          label="Highlight recent activity"
        />
        <Toggle
          checked={includeArchived}
          onChange={(checked) => {
            setIncludeArchived(checked);
            selection.clear();
          }}
          label="Show archived"
        />
      </div>

      <BulkActionBar selection={selection} />

      <div style={{ flex: 1, overflow: "auto", marginTop: 12 }}>
        {isLoading ? (
          <p style={{ padding: 24, color: "var(--text-muted)" }}>Loading…</p>
        ) : (
          <ApplicationsTable
            data={applications}
            selection={selection}
            onRowClick={(id) => {
              const app = applications.find((a) => a.id === id);
              if (app) setSelectedApp(app);
            }}
            onArchive={(id) => archive.mutate(id)}
            onDelete={(id) => {
              del.mutate(id, {
                onSuccess: () => {
                  if (selectedApp?.id === id) setSelectedApp(null);
                },
              });
            }}
            onStatusChange={(id, status) => update.mutate({ id, data: { status } })}
            highlightRecent={highlightRecent}
          />
        )}
      </div>

      {currentApp && (
        <ApplicationDetail application={currentApp} onClose={() => setSelectedApp(null)} />
      )}

      <Modal
        open={showNewForm}
        onClose={() => setShowNewForm(false)}
        title="New application"
      >
        <ApplicationForm
          onSubmit={(data) =>
            createApp.mutate(data, { onSuccess: () => setShowNewForm(false) })
          }
          onCancel={() => setShowNewForm(false)}
          isSubmitting={createApp.isPending}
        />
      </Modal>

      <ImportWizard open={showImport} onClose={() => setShowImport(false)} />
    </div>
  );
}
