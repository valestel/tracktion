from typing import Optional

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CompanyRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}
