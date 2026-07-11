import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitImport, previewImport } from "../../api/imports";
import type { ColumnMapping, ImportPreviewResponse, ImportRow } from "../../types";
import { Modal } from "../common/Modal";
import { ColumnMapper } from "./ColumnMapper";
import { ImportPreview } from "./ImportPreview";
import { Button } from "../common/Button";

type Step = "upload" | "map" | "preview" | "done";

interface ImportWizardProps {
  open: boolean;
  onClose: () => void;
}

function parseCsvHeaders(text: string): string[] {
  // Strip a UTF-8 BOM so headers match what the server parses (utf-8-sig)
  const firstLine = text.replace(/^\uFEFF/, "").split("\n")[0] ?? "";
  // Simple split — full parsing is done server-side
  return firstLine.split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
}

export function ImportWizard({ open, onClose }: ImportWizardProps) {
  const [step, setStep] = useState<Step>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<{ created: number; skipped: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  const previewMutation = useMutation({
    mutationFn: ({ file, mapping }: { file: File; mapping: ColumnMapping }) =>
      previewImport(file, mapping),
    onSuccess: (data) => {
      setPreview(data);
      setStep("preview");
    },
  });

  const commitMutation = useMutation({
    mutationFn: (rows: ImportRow[]) => commitImport(rows),
    onSuccess: (data) => {
      setResult(data);
      setStep("done");
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const handleFile = async (f: File) => {
    setFile(f);
    const text = await f.text();
    setCsvHeaders(parseCsvHeaders(text));
    setStep("map");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const reset = () => {
    setStep("upload");
    setFile(null);
    setCsvHeaders([]);
    setPreview(null);
    setResult(null);
    onClose();
  };

  const STEP_LABELS: Record<Step, string> = {
    upload: "Upload",
    map: "Map columns",
    preview: "Preview",
    done: "Done",
  };

  const titles: Record<Step, string> = {
    upload: "Import from CSV",
    map: "Map columns",
    preview: "Preview import",
    done: "Import complete",
  };

  return (
    <Modal open={open} onClose={reset} title={titles[step]}>
      <div className="import-step-indicator">
        {(["upload", "map", "preview"] as Step[]).map((s) => (
          <div
            key={s}
            className={`import-step ${step === s || (step === "done" && s === "preview") ? "active" : ""}`}
          >
            {STEP_LABELS[s]}
          </div>
        ))}
      </div>

      {step === "upload" && (
        <div
          className={`drop-zone ${dragOver ? "drag-over" : ""}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div style={{ fontSize: 32 }}>📂</div>
          <p>Drag & drop a CSV file here, or click to browse</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            style={{ display: "none" }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
        </div>
      )}

      {step === "map" && file && (
        <ColumnMapper
          csvHeaders={csvHeaders}
          onNext={(mapping) => previewMutation.mutate({ file, mapping })}
          onBack={() => setStep("upload")}
        />
      )}

      {step === "preview" && preview && (
        <ImportPreview
          preview={preview}
          onConfirm={(rows) => commitMutation.mutate(rows)}
          onBack={() => setStep("map")}
          isSubmitting={commitMutation.isPending}
        />
      )}

      {step === "done" && result && (
        <div style={{ textAlign: "center", padding: "16px 0" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
          <p style={{ fontSize: 15, fontWeight: 600 }}>
            {result.created} application{result.created !== 1 ? "s" : ""} imported
          </p>
          {result.skipped > 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 6 }}>
              {result.skipped} duplicate{result.skipped !== 1 ? "s" : ""} skipped
            </p>
          )}
          <Button variant="primary" style={{ marginTop: 20 }} onClick={reset}>
            Done
          </Button>
        </div>
      )}

      {previewMutation.isError && (
        <p style={{ color: "var(--danger)", fontSize: 13, marginTop: 12 }}>
          {(previewMutation.error as Error).message}
        </p>
      )}
    </Modal>
  );
}
