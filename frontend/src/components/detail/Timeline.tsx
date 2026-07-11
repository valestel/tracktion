import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getTimeline } from "../../api/analytics";
import {
  createStatusEvent,
  deleteStatusEvent,
  updateStatusEvent,
} from "../../api/statusEvents";
import type { StatusEventRead } from "../../types";
import { useStatuses } from "../../hooks/useStatuses";
import { Button } from "../common/Button";

interface TimelineProps {
  applicationId: number;
}

interface EventFormProps {
  initialStatus?: string;
  initialDate?: string; // YYYY-MM-DD
  onSave: (status: string, date: string) => void;
  onCancel: () => void;
  isSaving?: boolean;
}

function EventForm({ initialStatus, initialDate, onSave, onCancel, isSaving }: EventFormProps) {
  const { data: statuses = [] } = useStatuses();
  const [status, setStatus] = useState(initialStatus ?? "");
  const [date, setDate] = useState(initialDate ?? "");

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", margin: "8px 0" }}>
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="">— status —</option>
        {statuses.map((s) => (
          <option key={s.id} value={s.name}>
            {s.name}
          </option>
        ))}
      </select>
      <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <Button
        variant="primary"
        size="sm"
        disabled={!status || !date || isSaving}
        onClick={() => onSave(status, date)}
      >
        Save
      </Button>
      <Button variant="ghost" size="sm" onClick={onCancel}>
        Cancel
      </Button>
    </div>
  );
}

export function Timeline({ applicationId }: TimelineProps) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const qc = useQueryClient();

  const { data: events = [], isLoading } = useQuery({
    queryKey: ["timeline", applicationId],
    queryFn: () => getTimeline(applicationId),
  });

  const refresh = () => {
    // Editing the timeline can change the application's current status too
    qc.invalidateQueries({ queryKey: ["timeline", applicationId] });
    qc.invalidateQueries({ queryKey: ["applications"] });
  };

  const addMutation = useMutation({
    mutationFn: ({ status, date }: { status: string; date: string }) =>
      createStatusEvent(applicationId, { to_status: status, timestamp: `${date}T00:00:00` }),
    onSuccess: () => {
      setAdding(false);
      refresh();
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, status, date }: { id: number; status: string; date: string }) =>
      updateStatusEvent(id, { to_status: status, timestamp: `${date}T00:00:00` }),
    onSuccess: () => {
      setEditingId(null);
      refresh();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteStatusEvent(id),
    onSuccess: refresh,
  });

  const handleDelete = (event: StatusEventRead) => {
    if (confirm(`Remove "${event.to_status}" from the timeline?`)) {
      deleteMutation.mutate(event.id);
    }
  };

  if (isLoading) return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>;

  return (
    <div className="timeline">
      {events.length === 0 && !adding && (
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No history yet.</p>
      )}

      {events.map((event) =>
        editingId === event.id ? (
          <EventForm
            key={event.id}
            initialStatus={event.to_status}
            initialDate={event.timestamp.slice(0, 10)}
            onSave={(status, date) => editMutation.mutate({ id: event.id, status, date })}
            onCancel={() => setEditingId(null)}
            isSaving={editMutation.isPending}
          />
        ) : (
          <div key={event.id} className="timeline-item">
            <div className="timeline-transition">
              {event.from_status ? (
                <>
                  <span>{event.from_status}</span>
                  <span className="timeline-arrow">→</span>
                  <span>{event.to_status}</span>
                </>
              ) : (
                <span>Created as {event.to_status}</span>
              )}
              <Button
                variant="ghost"
                size="sm"
                style={{ marginLeft: 6 }}
                onClick={() => {
                  setAdding(false);
                  setEditingId(event.id);
                }}
              >
                ✎
              </Button>
              <Button variant="ghost" size="sm" onClick={() => handleDelete(event)}>
                ✕
              </Button>
            </div>
            <div className="timeline-time">
              {new Date(event.timestamp).toLocaleString()}
              {event.note && <> · {event.note}</>}
            </div>
          </div>
        )
      )}

      {adding ? (
        <EventForm
          onSave={(status, date) => addMutation.mutate({ status, date })}
          onCancel={() => setAdding(false)}
          isSaving={addMutation.isPending}
        />
      ) : (
        <Button
          variant="secondary"
          size="sm"
          style={{ marginTop: 8 }}
          onClick={() => {
            setEditingId(null);
            setAdding(true);
          }}
        >
          + Add event
        </Button>
      )}
    </div>
  );
}
