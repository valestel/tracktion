import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from sqlmodel import Session

from app.config import settings
from app.database import engine
from app.models.job_run import JobRun
from app.schemas.application import ApplicationUpdate
from app.services import application_service
from app.services.link_checker import USER_AGENT, Verdict, check_url, should_check

logger = logging.getLogger("tracktion.jobs.dead_links")

JOB_NAME = "dead_link_check"
CLOSED_STATUS = "role closed"


async def run_dead_link_check(session: Session | None = None) -> dict:
    if session is not None:
        return await _run(session)
    with Session(engine) as own_session:
        return await _run(own_session)


async def _run(session: Session) -> dict:
    applications = application_service.list_all(session, status="applied")
    to_check = [a for a in applications if should_check(a.link)]
    skipped = len(applications) - len(to_check)
    logger.info(
        "Dead-link check started: %d applied application(s), checking %d link(s), %d skipped",
        len(applications),
        len(to_check),
        skipped,
    )

    semaphore = asyncio.Semaphore(settings.link_check_concurrency)
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=settings.link_check_timeout_seconds,
        headers={"User-Agent": USER_AGENT},
    ) as client:

        async def check(link: str):
            async with semaphore:
                return await check_url(client, link)

        results = await asyncio.gather(*(check(a.link) for a in to_check))

    closed = inconclusive = 0
    for app, result in zip(to_check, results):
        if result.verdict is Verdict.CLOSED:
            application_service.update(session, app.id, ApplicationUpdate(status=CLOSED_STATUS))
            logger.info(
                'Application %d (%s — %s) marked "%s": %s (%s)',
                app.id,
                app.company_name,
                app.job_title,
                CLOSED_STATUS,
                app.link,
                result.reason,
            )
            closed += 1
        elif result.verdict is Verdict.INCONCLUSIVE:
            logger.info(
                "Application %d inconclusive, left unchanged: %s (%s)",
                app.id,
                app.link,
                result.reason,
            )
            inconclusive += 1

    summary = {
        "checked": len(to_check),
        "closed": closed,
        "inconclusive": inconclusive,
        "skipped": skipped,
    }
    logger.info("Dead-link check finished: %s", summary)
    return summary


def _is_due(session: Session) -> bool:
    run = session.get(JobRun, JOB_NAME)
    if run is None:
        return True
    return datetime.utcnow() - run.last_run_at >= timedelta(days=settings.link_check_interval_days)


def _record_run(session: Session) -> None:
    run = session.get(JobRun, JOB_NAME)
    if run is None:
        run = JobRun(job_name=JOB_NAME, last_run_at=datetime.utcnow())
    else:
        run.last_run_at = datetime.utcnow()
    session.add(run)
    session.commit()


async def scheduler_loop() -> None:
    # logger.info(
    #     "Dead-link scheduler started: runs every %d day(s), due-check every %d s",
    #     settings.link_check_interval_days,
    #     settings.link_check_poll_seconds,
    # )
    await asyncio.sleep(10)
    while True:
        try:
            with Session(engine) as session:
                due = _is_due(session)
            if due:
                await run_dead_link_check()
                # Recorded only after success so a failed run retries next poll.
                with Session(engine) as session:
                    _record_run(session)
        except Exception:
            logger.exception("Dead-link check failed; will retry at next poll")
        await asyncio.sleep(settings.link_check_poll_seconds)
