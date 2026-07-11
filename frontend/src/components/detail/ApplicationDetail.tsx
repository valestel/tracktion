import { useState } from "react";
import type { ApplicationRead } from "../../types";
import { toHref } from "../../utils/link";
import {
  useArchiveApplication,
  useDeleteApplication,
  useUnarchiveApplication,
  useUpdateApplication,
} from "../../hooks/useApplications";
import { StatusBadge } from "../table/StatusBadge";
import { Button } from "../common/Button";
import { Timeline } from "./Timeline";
import { ApplicationForm } from "./ApplicationForm";
import { CompanyRenameForm } from "./CompanyRenameForm";

interface ApplicationDetailProps {
  application: ApplicationRead;
  onClose: () => void;
}

export function ApplicationDetail({ application, onClose }: ApplicationDetailProps) {
  const [editing, setEditing] = useState(false);
  const [renamingCompany, setRenamingCompany] = useState(false);

  const update = useUpdateApplication();
  const archive = useArchiveApplication();
  const unarchive = useUnarchiveApplication();
  const del = useDeleteApplication();

  const handleUpdate = (data: Parameters<typeof update.mutate>[0]["data"]) => {
    update.mutate(
      { id: application.id, data },
      { onSuccess: () => setEditing(false) }
    );
  };

  const handleDelete = () => {
    if (confirm("Delete this application permanently?")) {
      del.mutate(application.id, { onSuccess: onClose });
    }
  };

  return (
    <div className="detail-panel">
      <div className="detail-header">
        <div>
          <h2>{application.job_title}</h2>
          {renamingCompany ? (
            <CompanyRenameForm
              companyId={application.company_id}
              initialName={application.company_name}
              initialDescription={application.company_description}
              onDone={() => setRenamingCompany(false)}
            />
          ) : (
            <>
              <div className="detail-meta">
                {application.company_name}
                {!editing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    style={{ marginLeft: 6 }}
                    onClick={() => setRenamingCompany(true)}
                  >
                    ✎
                  </Button>
                )}
              </div>
              {application.company_description && (
                <div className="detail-meta" style={{ marginTop: 4 }}>
                  {application.company_description}
                </div>
              )}
            </>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ✕
        </Button>
      </div>

      <div className="detail-body">
        {editing ? (
          <ApplicationForm
            initialValues={{
              job_title: application.job_title,
              application_date: application.application_date,
              link: application.link ?? "",
              status: application.status,
              notes: application.notes ?? "",
            }}
            initialCompany={{
              id: application.company_id,
              name: application.company_name,
              description: application.company_description,
            }}
            onSubmit={handleUpdate}
            onCancel={() => setEditing(false)}
            isSubmitting={update.isPending}
          />
        ) : (
          <>
            <div className="detail-field">
              <div className="label">Status</div>
              <div className="value">
                <StatusBadge status={application.status} />
              </div>
            </div>

            <div className="detail-field">
              <div className="label">Applied</div>
              <div className="value">
                {new Date(application.application_date).toLocaleDateString()}
              </div>
            </div>

            {application.link && (
              <div className="detail-field">
                <div className="label">Link</div>
                <div className="value">
                  <a href={toHref(application.link)} target="_blank" rel="noopener noreferrer">
                    {application.link}
                  </a>
                </div>
              </div>
            )}

            {application.notes && (
              <div className="detail-field">
                <div className="label">Notes</div>
                <div className="value" style={{ whiteSpace: "pre-wrap" }}>
                  {application.notes}
                </div>
              </div>
            )}

            <div className="detail-field" style={{ marginTop: 24 }}>
              <div className="label" style={{ marginBottom: 12 }}>
                Timeline
              </div>
              <Timeline applicationId={application.id} />
            </div>
          </>
        )}
      </div>

      {!editing && (
        <div className="detail-actions">
          <Button variant="secondary" size="sm" onClick={() => setEditing(true)}>
            Edit
          </Button>
          {application.archived_at ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => unarchive.mutate(application.id)}
            >
              Unarchive
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => archive.mutate(application.id)}
            >
              Archive
            </Button>
          )}
          <Button variant="danger" size="sm" onClick={handleDelete} style={{ marginLeft: "auto" }}>
            Delete
          </Button>
        </div>
      )}
    </div>
  );
}
