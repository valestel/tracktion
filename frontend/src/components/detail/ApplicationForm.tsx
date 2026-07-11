import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import type { ApplicationCreate } from "../../types";
import { useCompanies, useCreateCompany } from "../../hooks/useCompanies";
import { useStatuses } from "../../hooks/useStatuses";
import { Button } from "../common/Button";
import { CompanyCombobox } from "./CompanyCombobox";
import { validateLinkOrEmail } from "../../utils/link";

interface FormValues {
  job_title: string;
  application_date: string;
  link: string;
  status: string;
  notes: string;
}

interface InitialCompany {
  id: number;
  name: string;
  description: string | null;
}

interface ApplicationFormProps {
  initialValues?: Partial<FormValues>;
  initialCompany?: InitialCompany;
  onSubmit: (data: ApplicationCreate) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

function todayIsoDate() {
  return new Date().toLocaleDateString("en-CA"); // yyyy-mm-dd in local time
}

export function ApplicationForm({
  initialValues,
  initialCompany,
  onSubmit,
  onCancel,
  isSubmitting,
}: ApplicationFormProps) {
  const { data: companies = [] } = useCompanies();
  const { data: statuses = [] } = useStatuses();
  const createCompany = useCreateCompany();

  const [companyText, setCompanyText] = useState(initialCompany?.name ?? "");
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(
    initialCompany?.id ?? null
  );
  const [companyDescription, setCompanyDescription] = useState(
    initialCompany?.description ?? ""
  );
  const [companyError, setCompanyError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: {
      application_date: todayIsoDate(),
      status: "applied",
      ...initialValues,
    },
  });

  useEffect(() => {
    if (initialValues) reset(initialValues);
  }, [initialValues, reset]);

  useEffect(() => {
    if (initialCompany) {
      setCompanyText(initialCompany.name);
      setSelectedCompanyId(initialCompany.id);
      setCompanyDescription(initialCompany.description ?? "");
    }
  }, [initialCompany]);

  const onValid = async (values: FormValues) => {
    const name = companyText.trim();
    if (!name) {
      setCompanyError("Required");
      return;
    }

    let resolvedCompanyId: number;
    const selected =
      selectedCompanyId != null ? companies.find((c) => c.id === selectedCompanyId) : undefined;

    if (selected && selected.name.toLowerCase() === name.toLowerCase()) {
      resolvedCompanyId = selected.id;
    } else {
      const existing = companies.find((c) => c.name.toLowerCase() === name.toLowerCase());
      if (existing) {
        resolvedCompanyId = existing.id;
      } else {
        try {
          const company = await createCompany.mutateAsync({
            name,
            description: companyDescription.trim() || undefined,
          });
          resolvedCompanyId = company.id;
        } catch {
          setCompanyError("Could not create company");
          return;
        }
      }
    }

    onSubmit({
      company_id: resolvedCompanyId,
      job_title: values.job_title,
      application_date: values.application_date,
      link: values.link || undefined,
      status: values.status,
      notes: values.notes || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit(onValid)}>
      <div className="form-group">
        <label>Company *</label>
        <CompanyCombobox
          companies={companies}
          text={companyText}
          onTextChange={(text) => {
            setCompanyText(text);
            setCompanyError(null);
          }}
          selectedCompanyId={selectedCompanyId}
          onSelectCompany={(company) => setSelectedCompanyId(company?.id ?? null)}
          description={companyDescription}
          onDescriptionChange={setCompanyDescription}
          error={companyError}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Role *</label>
          <input
            {...register("job_title", { required: "Required" })}
            placeholder="AI Engineer"
          />
          {errors.job_title && <span className="form-error">{errors.job_title.message}</span>}
        </div>
        <div className="form-group">
          <label>Date applied *</label>
          <input type="date" {...register("application_date", { required: "Required" })} />
          {errors.application_date && (
            <span className="form-error">{errors.application_date.message}</span>
          )}
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Status *</label>
          <select {...register("status", { required: "Required" })}>
            <option value="">Select status…</option>
            {statuses.map((s) => (
              <option key={s.id} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
          {errors.status && <span className="form-error">{errors.status.message}</span>}
        </div>
        <div className="form-group">
          <label>Link / Email</label>
          <input
            {...register("link", { validate: validateLinkOrEmail })}
            placeholder="https://… or name@company.com"
          />
          {errors.link && <span className="form-error">{errors.link.message}</span>}
        </div>
      </div>

      <div className="form-group">
        <label>Notes</label>
        <textarea {...register("notes")} placeholder="Any additional context…" />
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={isSubmitting || createCompany.isPending}>
          {isSubmitting || createCompany.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}
