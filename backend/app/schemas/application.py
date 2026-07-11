from datetime import date, datetime
from typing import Optional, Text

from pydantic import BaseModel, field_validator

from app.core.validators import is_valid_link_or_email


class _LinkValidationMixin:
    @field_validator("link")
    @classmethod
    def validate_link(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if not is_valid_link_or_email(v):
            raise ValueError("link must be a valid URL (http:// or https://) or an email address")
        return v


class ApplicationCreate(_LinkValidationMixin, BaseModel):
    company_id: int
    job_title: str
    application_date: date
    link: Optional[str] = None
    status: str
    notes: Optional[Text] = None


class ApplicationUpdate(_LinkValidationMixin, BaseModel):
    company_id: Optional[int] = None
    job_title: Optional[str] = None
    application_date: Optional[date] = None
    link: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[Text] = None


class ApplicationRead(BaseModel):
    id: int
    company_id: int
    company_name: str
    company_description: Optional[str] = None
    job_title: str
    application_date: date
    link: Optional[str] = None
    status: str
    notes: Optional[Text] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_status_change_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BulkUpdate(BaseModel):
    ids: list[int]
    status: Optional[str] = None
    archived: Optional[bool] = None


class BulkDelete(BaseModel):
    ids: list[int]
