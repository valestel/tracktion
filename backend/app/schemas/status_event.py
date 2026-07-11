from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatusEventCreate(BaseModel):
    to_status: str
    timestamp: datetime


class StatusEventUpdate(BaseModel):
    to_status: Optional[str] = None
    timestamp: Optional[datetime] = None
