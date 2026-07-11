from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ColumnMapping(BaseModel):
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    job_title: Optional[str] = None
    application_date: Optional[str] = None
    link: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class StatusEventDraft(BaseModel):
    from_status: Optional[str] = None
    to_status: str
    timestamp: Optional[datetime] = None


class ImportRow(BaseModel):
    company_name: str
    company_description: Optional[str] = None
    job_title: str
    application_date: date
    link: Optional[str] = None
    status: str
    notes: Optional[str] = None
    is_duplicate: bool = False
    status_events: list[StatusEventDraft] = []


class ImportPreviewResponse(BaseModel):
    rows: list[ImportRow]
    errors: list[str]
    warnings: list[str] = []
    duplicate_count: int


class ImportCommitResponse(BaseModel):
    created: int
    skipped: int
