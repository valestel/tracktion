from datetime import date, datetime
from typing import TYPE_CHECKING, Optional, Text

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.status_event import StatusEvent


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id", index=True)
    job_title: str
    application_date: date
    link: Optional[str] = None
    status: str = Field(index=True)
    notes: Optional[Text] = None
    archived_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_status_change_at: Optional[datetime] = Field(default=None)

    company: Optional["Company"] = Relationship(back_populates="applications")
    status_events: list["StatusEvent"] = Relationship(
        back_populates="application",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
