from typing import Optional

from sqlmodel import Field, SQLModel


class Status(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    color: Optional[str] = None
    sort_order: int = Field(default=0)
