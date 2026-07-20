from datetime import datetime, time

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.application import Application
from app.models.status_event import StatusEvent
from app.repositories import application_repo
from app.repositories import company_repo
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    BulkDelete,
    BulkUpdate,
)
from app.schemas.imports import StatusEventDraft


def _to_read(app: Application) -> ApplicationRead:
    company_name = app.company.name if app.company else ""
    company_description = app.company.description if app.company else None
    return ApplicationRead(
        id=app.id,  # type: ignore[arg-type]
        company_id=app.company_id,
        company_name=company_name,
        company_description=company_description,
        job_title=app.job_title,
        application_date=app.application_date,
        link=app.link,
        status=app.status,
        notes=app.notes,
        archived_at=app.archived_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
        last_status_change_at=app.last_status_change_at,
    )


def _write_status_event(
    session: Session,
    application_id: int,
    from_status: str | None,
    to_status: str,
    note: str | None = None,
    timestamp: datetime | None = None,
) -> None:
    kwargs = dict(
        application_id=application_id,
        from_status=from_status,
        to_status=to_status,
        note=note,
    )
    if timestamp is not None:
        kwargs["timestamp"] = timestamp
    event = StatusEvent(**kwargs)
    session.add(event)


def get(session: Session, app_id: int) -> ApplicationRead:
    app = application_repo.get(session, app_id)
    if not app:
        raise NotFoundError(app_id)
    return _to_read(app)


def list_all(
    session: Session,
    *,
    include_archived: bool = False,
    company_id: int | None = None,
    status: str | None = None,
    ever_status: list[str] | None = None,
    ever_status_match_all: bool = False,
) -> list[ApplicationRead]:
    apps = application_repo.list_all(
        session,
        include_archived=include_archived,
        company_id=company_id,
        status=status,
        ever_status=ever_status,
        ever_status_match_all=ever_status_match_all,
    )
    return [_to_read(a) for a in apps]


def create(
    session: Session,
    data: ApplicationCreate,
    status_events: list[StatusEventDraft] | None = None,
) -> ApplicationRead:
    if not company_repo.get(session, data.company_id):
        raise NotFoundError(data.company_id)
    app = Application(**data.model_dump())
    session.add(app)
    session.flush()  # get app.id before writing event(s)
    if status_events:
        for ev in status_events:
            _write_status_event(session, app.id, ev.from_status, ev.to_status, timestamp=ev.timestamp)  # type: ignore[arg-type]
    else:
        # Date the creation event at the application date, not entry time,
        # so backfilled applications keep a truthful timeline.
        _write_status_event(
            session,
            app.id,  # type: ignore[arg-type]
            None,
            app.status,
            timestamp=datetime.combine(app.application_date, time.min),
        )
    session.commit()
    session.refresh(app)
    return _to_read(app)


def update(session: Session, app_id: int, data: ApplicationUpdate) -> ApplicationRead:
    app = application_repo.get(session, app_id)
    if not app:
        raise NotFoundError(app_id)

    prev_status = app.status
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    app.updated_at = datetime.utcnow()

    if data.status is not None and data.status != prev_status:
        _write_status_event(session, app.id, prev_status, data.status)  # type: ignore[arg-type]
        app.last_status_change_at = datetime.utcnow()

    session.add(app)
    session.commit()
    session.refresh(app)
    return _to_read(app)


def archive(session: Session, app_id: int) -> ApplicationRead:
    app = application_repo.get(session, app_id)
    if not app:
        raise NotFoundError(app_id)
    app.archived_at = datetime.utcnow()
    app.updated_at = datetime.utcnow()
    session.add(app)
    session.commit()
    session.refresh(app)
    return _to_read(app)


def unarchive(session: Session, app_id: int) -> ApplicationRead:
    app = application_repo.get(session, app_id)
    if not app:
        raise NotFoundError(app_id)
    app.archived_at = None
    app.updated_at = datetime.utcnow()
    session.add(app)
    session.commit()
    session.refresh(app)
    return _to_read(app)


def delete(session: Session, app_id: int) -> None:
    if not application_repo.delete(session, app_id):
        raise NotFoundError(app_id)


def bulk_delete(session: Session, data: BulkDelete) -> None:
    apps = application_repo.bulk_get(session, data.ids)
    company_ids = {app.company_id for app in apps}
    for app in apps:
        session.delete(app)
    session.flush()
    for company_id in company_ids:
        remaining = application_repo.list_all(
            session, include_archived=True, company_id=company_id
        )
        if not remaining:
            company = company_repo.get(session, company_id)
            if company:
                session.delete(company)
    session.commit()


def bulk_update(session: Session, data: BulkUpdate) -> list[ApplicationRead]:
    apps = application_repo.bulk_get(session, data.ids)
    results = []
    for app in apps:
        update_data = ApplicationUpdate()
        if data.status is not None:
            update_data.status = data.status
        results.append(update(session, app.id, update_data))  # type: ignore[arg-type]

    if data.archived is True:
        for app in apps:
            if app.archived_at is None:
                results = [r for r in results if r.id != app.id]
                results.append(archive(session, app.id))  # type: ignore[arg-type]
    elif data.archived is False:
        for app in apps:
            if app.archived_at is not None:
                results = [r for r in results if r.id != app.id]
                results.append(unarchive(session, app.id))  # type: ignore[arg-type]

    return results
