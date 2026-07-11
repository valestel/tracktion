from datetime import datetime

from sqlmodel import Session, select

from app.core.csv_parser import normalize_status
from app.core.exceptions import NotFoundError, ValidationError
from app.models.status import Status
from app.models.status_event import StatusEvent
from app.repositories import application_repo, status_event_repo
from app.schemas.analytics import StatusEventRead
from app.schemas.status_event import StatusEventCreate, StatusEventUpdate


def _to_read(event: StatusEvent) -> StatusEventRead:
    return StatusEventRead(
        id=event.id,  # type: ignore[arg-type]
        application_id=event.application_id,
        from_status=event.from_status,
        to_status=event.to_status,
        timestamp=event.timestamp.isoformat(),
        note=event.note,
    )


def _validate_status(session: Session, status: str) -> str:
    known = [s.name for s in session.exec(select(Status)).all()]
    matched = normalize_status(status, known)
    if matched is None:
        raise ValidationError(f"Unknown status '{status}'")
    return matched


def _rechain(session: Session, application_id: int) -> None:
    """Rebuild from_status links after events changed, and sync the application.

    Events are ordered by timestamp; the application's current status follows
    the latest event so table, analytics and timeline stay consistent.
    """
    app = application_repo.get(session, application_id)
    if not app:
        raise NotFoundError(application_id)

    events = status_event_repo.list_for_application(session, application_id)
    prev: str | None = None
    for event in events:
        if event.from_status != prev:
            event.from_status = prev
            session.add(event)
        prev = event.to_status

    if events:
        app.status = events[-1].to_status
        app.last_status_change_at = events[-1].timestamp if len(events) > 1 else None
    app.updated_at = datetime.utcnow()
    session.add(app)


def create(session: Session, application_id: int, data: StatusEventCreate) -> StatusEventRead:
    if not application_repo.get(session, application_id):
        raise NotFoundError(application_id)
    to_status = _validate_status(session, data.to_status)

    event = StatusEvent(
        application_id=application_id,
        from_status=None,  # set by _rechain
        to_status=to_status,
        timestamp=data.timestamp,
    )
    session.add(event)
    session.flush()
    _rechain(session, application_id)
    session.commit()
    session.refresh(event)
    return _to_read(event)


def update(session: Session, event_id: int, data: StatusEventUpdate) -> StatusEventRead:
    event = status_event_repo.get(session, event_id)
    if not event:
        raise NotFoundError(event_id)

    if data.to_status is not None:
        event.to_status = _validate_status(session, data.to_status)
    if data.timestamp is not None:
        event.timestamp = data.timestamp

    session.add(event)
    session.flush()
    _rechain(session, event.application_id)
    session.commit()
    session.refresh(event)
    return _to_read(event)


def delete(session: Session, event_id: int) -> None:
    event = status_event_repo.get(session, event_id)
    if not event:
        raise NotFoundError(event_id)

    application_id = event.application_id
    session.delete(event)
    session.flush()
    _rechain(session, application_id)
    session.commit()
