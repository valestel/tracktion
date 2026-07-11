from datetime import datetime

import pytest
from sqlmodel import Session, select

from app.core.exceptions import NotFoundError, ValidationError
from app.models.application import Application
from app.models.status import Status
from app.models.status_event import StatusEvent
from app.schemas.status_event import StatusEventCreate, StatusEventUpdate
from app.services import status_event_service


@pytest.fixture(autouse=True)
def _statuses(session: Session):
    for name in ("applied", "screening call", "interview", "offer", "rejected"):
        session.add(Status(name=name, color=None, sort_order=0))
    session.commit()


def _events(session: Session, app_id: int) -> list[StatusEvent]:
    stmt = (
        select(StatusEvent)
        .where(StatusEvent.application_id == app_id)
        .order_by(StatusEvent.timestamp, StatusEvent.id)
    )
    return list(session.exec(stmt).all())


def test_create_event_uses_provided_timestamp(session: Session, sample_application):
    provided = datetime(2026, 2, 10)
    result = status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="screening call", timestamp=provided),
    )
    event = session.get(StatusEvent, result.id)
    assert event.timestamp == provided  # not utcnow()


def test_create_event_rechains_and_updates_application_status(session: Session, sample_application):
    status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="screening call", timestamp=datetime(2026, 2, 10)),
    )
    status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="rejected", timestamp=datetime(2026, 3, 1)),
    )

    events = _events(session, sample_application.id)
    assert [(e.from_status, e.to_status) for e in events] == [
        (None, "applied"),
        ("applied", "screening call"),
        ("screening call", "rejected"),
    ]
    app = session.get(Application, sample_application.id)
    assert app.status == "rejected"
    assert app.last_status_change_at == datetime(2026, 3, 1)


def test_create_event_in_the_past_is_inserted_in_order(session: Session, sample_application):
    status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="rejected", timestamp=datetime(2026, 3, 1)),
    )
    # inserted afterwards, but dated between creation and rejection
    status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="screening call", timestamp=datetime(2026, 2, 10)),
    )

    events = _events(session, sample_application.id)
    assert [e.to_status for e in events] == ["applied", "screening call", "rejected"]
    app = session.get(Application, sample_application.id)
    assert app.status == "rejected"


def test_create_event_rejects_unknown_status(session: Session, sample_application):
    with pytest.raises(ValidationError):
        status_event_service.create(
            session,
            sample_application.id,
            StatusEventCreate(to_status="nonexistent", timestamp=datetime(2026, 2, 10)),
        )


def test_create_event_missing_application_raises(session: Session):
    with pytest.raises(NotFoundError):
        status_event_service.create(
            session, 999, StatusEventCreate(to_status="applied", timestamp=datetime(2026, 2, 10))
        )


def test_update_event_date_reorders_chain(session: Session, sample_application):
    screening = status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="screening call", timestamp=datetime(2026, 2, 10)),
    )
    status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="interview", timestamp=datetime(2026, 3, 1)),
    )

    # move the screening call after the interview
    status_event_service.update(
        session, screening.id, StatusEventUpdate(timestamp=datetime(2026, 3, 15))
    )

    events = _events(session, sample_application.id)
    assert [e.to_status for e in events] == ["applied", "interview", "screening call"]
    app = session.get(Application, sample_application.id)
    assert app.status == "screening call"


def test_update_event_status(session: Session, sample_application):
    event = status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="screening call", timestamp=datetime(2026, 2, 10)),
    )
    status_event_service.update(session, event.id, StatusEventUpdate(to_status="interview"))

    events = _events(session, sample_application.id)
    assert events[-1].to_status == "interview"
    app = session.get(Application, sample_application.id)
    assert app.status == "interview"


def test_delete_event_rechains(session: Session, sample_application):
    screening = status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="screening call", timestamp=datetime(2026, 2, 10)),
    )
    status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="rejected", timestamp=datetime(2026, 3, 1)),
    )

    status_event_service.delete(session, screening.id)

    events = _events(session, sample_application.id)
    assert [(e.from_status, e.to_status) for e in events] == [
        (None, "applied"),
        ("applied", "rejected"),
    ]


def test_delete_last_event_reverts_application_status(session: Session, sample_application):
    rejected = status_event_service.create(
        session,
        sample_application.id,
        StatusEventCreate(to_status="rejected", timestamp=datetime(2026, 3, 1)),
    )
    status_event_service.delete(session, rejected.id)

    app = session.get(Application, sample_application.id)
    assert app.status == "applied"
    assert app.last_status_change_at is None