from datetime import datetime

from sqlmodel import Field, SQLModel


class JobRun(SQLModel, table=True):
    __tablename__ = "job_run"

    job_name: str = Field(primary_key=True)
    last_run_at: datetime  # UTC; written only when a run completes successfully
