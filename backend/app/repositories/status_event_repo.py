from sqlmodel import Session, select

from app.models.status_event import StatusEvent


def list_for_application(session: Session, application_id: int) -> list[StatusEvent]:
    stmt = (
        select(StatusEvent)
        .where(StatusEvent.application_id == application_id)
        .order_by(StatusEvent.timestamp, StatusEvent.id)
    )
    return list(session.exec(stmt).all())


def get(session: Session, event_id: int) -> StatusEvent | None:
    return session.get(StatusEvent, event_id)


def create(session: Session, event: StatusEvent) -> StatusEvent:
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def list_all_ordered(session: Session) -> list[StatusEvent]:
    stmt = select(StatusEvent).order_by(
        StatusEvent.application_id, StatusEvent.timestamp, StatusEvent.id
    )
    return list(session.exec(stmt).all())
