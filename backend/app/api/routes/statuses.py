from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import SessionDep
from app.models.status import Status

router = APIRouter(prefix="/statuses", tags=["statuses"])


@router.get("", response_model=list[dict])
def list_statuses(session: SessionDep):
    statuses = session.exec(select(Status).order_by(Status.sort_order)).all()
    return [
        {"id": s.id, "name": s.name, "color": s.color, "sort_order": s.sort_order}
        for s in statuses
    ]
