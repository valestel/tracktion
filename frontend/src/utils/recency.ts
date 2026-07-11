import type { ApplicationRead } from "../types";

// Substring match, case-insensitive — covers custom status names too
// (e.g. "final interview", "phone screen", "take-home task").
const HIGHLIGHT_PATTERNS = [
  "applied",
  "interview",
  "offer",
  "waiting",
  "screen",
  "intro",
  "take-home",
  "take home",
];

const DAY_MS = 86_400_000;

export function isHighlightableStatus(status: string): boolean {
  const s = status.trim().toLowerCase();
  return HIGHLIGHT_PATTERNS.some((p) => s.includes(p));
}

function daysSince(isoDate: string): number {
  return (Date.now() - new Date(isoDate).getTime()) / DAY_MS;
}

export function getRecencyTint(app: ApplicationRead): string | undefined {
  if (!isHighlightableStatus(app.status)) return undefined;

  // Recency is driven by whichever happened more recently: applying, or an
  // actual status change (last_status_change_at is only set on real
  // transitions, not on initial creation — so it's null until a status
  // change has actually occurred).
  const appliedDays = daysSince(app.application_date);
  const statusChangeDays = app.last_status_change_at
    ? daysSince(app.last_status_change_at)
    : Infinity;
  const days = Math.min(appliedDays, statusChangeDays);

  if (days < 7) return "rgba(20, 184, 166, 0.14)";
  if (days < 14) return "rgba(20, 184, 166, 0.06)";
  return undefined;
}
