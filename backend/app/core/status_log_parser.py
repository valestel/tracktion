import re
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional

from app.core.csv_parser import normalize_status
from app.schemas.imports import StatusEventDraft

_ENTRY_SEPARATOR_RE = re.compile(r"[,\n]+")
_ENTRY_RE = re.compile(
    r"^\s*(?P<date>\d{1,2}\.\d{1,2}(?:\.\d{4})?)\s*-\s*(?P<status>.+?)\s*$"
)


@dataclass
class ParsedStatusEntry:
    date: date
    to_status: str


@dataclass
class ParsedStatusLog:
    entries: list[ParsedStatusEntry]
    # Chunks that look like log entries ("date - text") but could not be
    # converted to an event (unknown status or invalid date).
    unrecognized: list[str]


def parse_log_date(val: str, year_hint: int) -> Optional[date]:
    parts = val.strip().split(".")
    try:
        if len(parts) == 3:
            if len(parts[2]) != 4:
                return None
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            year = year_hint
        else:
            return None
        return date(year, month, day)
    except ValueError:
        return None


def parse_status_log(
    notes: Optional[str], application_date: date, known_statuses: list[str]
) -> ParsedStatusLog:
    if not notes:
        return ParsedStatusLog(entries=[], unrecognized=[])

    entries: list[ParsedStatusEntry] = []
    unrecognized: list[str] = []
    for chunk in _ENTRY_SEPARATOR_RE.split(notes):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = _ENTRY_RE.match(chunk)
        if not match:
            continue  # plain notes text, not a log entry
        parsed_date = parse_log_date(match.group("date"), application_date.year)
        matched_status = (
            normalize_status(match.group("status"), known_statuses)
            if parsed_date is not None
            else None
        )
        if parsed_date is None or matched_status is None:
            unrecognized.append(chunk)
            continue
        entries.append(ParsedStatusEntry(date=parsed_date, to_status=matched_status))

    entries.sort(key=lambda e: e.date)
    return ParsedStatusLog(entries=entries, unrecognized=unrecognized)


def build_event_chain(
    entries: list[ParsedStatusEntry],
    final_status: str,
    application_date: date,
    initial_status: Optional[str] = None,
) -> list[StatusEventDraft]:
    """Build the StatusEvent chain for an imported application.

    The chain starts at initial_status (e.g. "applied") on application_date,
    walks through the parsed log entries, and ends at final_status (the CSV
    status column). A timestamp of None means "resolve at write time".
    """
    chain: list[StatusEventDraft] = []
    prev_status: Optional[str] = None

    if initial_status:
        chain.append(
            StatusEventDraft(
                from_status=None,
                to_status=initial_status,
                timestamp=datetime.combine(application_date, time.min),
            )
        )
        prev_status = initial_status

    for entry in entries:
        if entry.to_status == prev_status:
            continue
        chain.append(
            StatusEventDraft(
                from_status=prev_status,
                to_status=entry.to_status,
                timestamp=datetime.combine(entry.date, time.min),
            )
        )
        prev_status = entry.to_status

    if prev_status != final_status:
        chain.append(StatusEventDraft(from_status=prev_status, to_status=final_status, timestamp=None))

    return chain
