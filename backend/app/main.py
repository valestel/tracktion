import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.jobs.dead_link_job import scheduler_loop

    _configure_logging()
    init_db()
    _seed_default_statuses()
    scheduler_task = asyncio.create_task(scheduler_loop(), name="dead-link-scheduler")
    yield
    scheduler_task.cancel()
    with suppress(asyncio.CancelledError):
        await scheduler_task


def _configure_logging() -> None:
    # uvicorn only configures its own loggers; give tracktion.* a console handler
    # so job logs show up alongside uvicorn output.
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s"
        )


def _seed_default_statuses() -> None:
    from sqlmodel import Session, select

    from app.database import engine
    from app.models.status import Status

    with Session(engine) as session:
        existing = session.exec(select(Status)).all()
        existing_names = {s.name for s in existing}
        for name, color, sort_order in settings.default_statuses:
            if name not in existing_names:
                session.add(Status(name=name, color=color, sort_order=sort_order))
        session.commit()


def create_app() -> FastAPI:
    app = FastAPI(title="Tracktion", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    from app.api.routes import (
        analytics,
        applications,
        companies,
        imports,
        jobs,
        status_events,
        statuses,
    )

    app.include_router(applications.router, prefix="/api/v1")
    app.include_router(companies.router, prefix="/api/v1")
    app.include_router(imports.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(statuses.router, prefix="/api/v1")
    app.include_router(status_events.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")

    return app


app = create_app()
