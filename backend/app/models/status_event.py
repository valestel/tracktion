from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.application import Application


class StatusEvent(SQLModel, table=True):
    __tablename__ = "status_event"

    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="application.id", index=True, ondelete="CASCADE")
    from_status: Optional[str] = None
    to_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    note: Optional[str] = None

    application: Optional["Application"] = Relationship(back_populates="status_events")
