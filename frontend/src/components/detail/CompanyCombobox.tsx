import { useEffect, useRef, useState } from "react";
import type { Company } from "../../types";

interface CompanyComboboxProps {
  companies: Company[];
  text: string;
  onTextChange: (text: string) => void;
  selectedCompanyId: number | null;
  onSelectCompany: (company: Company | null) => void;
  description: string;
  onDescriptionChange: (description: string) => void;
  error: string | null;
}

export function CompanyCombobox({
  companies,
  text,
  onTextChange,
  selectedCompanyId,
  onSelectCompany,
  description,
  onDescriptionChange,
  error,
}: CompanyComboboxProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  const trimmed = text.trim();
  const suggestions = trimmed
    ? companies
        .filter((c) => c.name.toLowerCase().includes(trimmed.toLowerCase()))
        .slice(0, 8)
    : [];

  const selected =
    selectedCompanyId != null ? companies.find((c) => c.id === selectedCompanyId) : undefined;
  const matchedCompany =
    selected && selected.name.toLowerCase() === trimmed.toLowerCase()
      ? selected
      : companies.find((c) => c.name.toLowerCase() === trimmed.toLowerCase());

  const showSuggestions = open && trimmed !== "" && suggestions.length > 0;

  const selectCompany = (company: Company) => {
    onTextChange(company.name);
    onSelectCompany(company);
    setOpen(false);
  };

  return (
    <div className="company-combobox">
      <div className="dropdown" ref={ref}>
        <input
          placeholder="Company name"
          value={text}
          onFocus={() => setOpen(true)}
          onChange={(e) => {
            onSelectCompany(null);
            onTextChange(e.target.value);
            setOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") setOpen(false);
          }}
        />
        {showSuggestions && (
          <div className="dropdown-menu">
            {suggestions.map((c) => (
              <div key={c.id} className="dropdown-item" onMouseDown={() => selectCompany(c)}>
                {c.name}
              </div>
            ))}
          </div>
        )}
      </div>

      {error ? (
        <span className="form-error">{error}</span>
      ) : matchedCompany ? (
        <span className="company-match-hint">Existing company</span>
      ) : trimmed ? (
        <span className="company-match-hint">Will be added as a new company</span>
      ) : null}

      <textarea
        placeholder="Company description (optional)"
        value={matchedCompany ? matchedCompany.description ?? "" : description}
        onChange={(e) => onDescriptionChange(e.target.value)}
        readOnly={!!matchedCompany}
      />
    </div>
  );
}
