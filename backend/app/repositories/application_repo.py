from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.application import Application
from app.models.status_event import StatusEvent


def get(session: Session, app_id: int) -> Optional[Application]:
    return session.get(Application, app_id)


def list_all(
    session: Session,
    *,
    include_archived: bool = False,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    ever_status: Optional[list[str]] = None,
    ever_status_match_all: bool = False,
) -> list[Application]:
    stmt = select(Application)
    if not include_archived:
        stmt = stmt.where(Application.archived_at.is_(None))  # type: ignore[union-attr]
    if company_id is not None:
        stmt = stmt.where(Application.company_id == company_id)
    if status is not None:
        stmt = stmt.where(Application.status == status)
    if ever_status:
        subq = select(StatusEvent.application_id).where(StatusEvent.to_status.in_(ever_status))
        if ever_status_match_all:
            subq = subq.group_by(StatusEvent.application_id).having(
                func.count(func.distinct(StatusEvent.to_status)) == len(ever_status)
            )
        stmt = stmt.where(Application.id.in_(subq))  # type: ignore[union-attr]
    stmt = stmt.order_by(Application.application_date.desc(), Application.created_at.desc())  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


def create(session: Session, application: Application) -> Application:
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def update(session: Session, application: Application) -> Application:
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def delete(session: Session, app_id: int) -> bool:
    application = session.get(Application, app_id)
    if not application:
        return False
    session.delete(application)
    session.commit()
    return True


def bulk_get(session: Session, ids: list[int]) -> list[Application]:
    if not ids:
        return []
    stmt = select(Application).where(Application.id.in_(ids))  # type: ignore[union-attr]
    return list(session.exec(stmt).all())
