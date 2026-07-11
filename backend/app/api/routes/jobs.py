from fastapi import APIRouter

from app.jobs.dead_link_job import run_dead_link_check

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/check-links")
async def trigger_link_check() -> dict:
    """Run the dead-link check immediately (does not affect the weekly schedule)."""
    return await run_dead_link_check()
