import { useState } from "react";
import { useUpdateCompany } from "../../hooks/useCompanies";
import { useApplications } from "../../hooks/useApplications";
import { Button } from "../common/Button";

interface CompanyRenameFormProps {
  companyId: number;
  initialName: string;
  initialDescription: string | null;
  onDone: () => void;
}

export function CompanyRenameForm({
  companyId,
  initialName,
  initialDescription,
  onDone,
}: CompanyRenameFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription ?? "");

  const update = useUpdateCompany();
  const affected = useApplications({ company_id: companyId, include_archived: true });

  const handleSave = () => {
    update.mutate(
      { id: companyId, data: { name, description } },
      { onSuccess: onDone }
    );
  };

  return (
    <div className="form-group" style={{ marginTop: 4 }}>
      <input
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Company name"
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Company description (optional)"
      />
      {update.error && (
        <span className="form-error">{update.error.message}</span>
      )}
      {affected.data && affected.data.length > 1 && (
        <div className="company-match-hint">
          Updates the company for {affected.data.length} applications
        </div>
      )}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
        <Button variant="secondary" size="sm" onClick={onDone} disabled={update.isPending}>
          Cancel
        </Button>
        <Button variant="primary" size="sm" onClick={handleSave} disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </div>
  );
}
