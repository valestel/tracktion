from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.analytics import StatusEventRead
from app.schemas.status_event import StatusEventCreate, StatusEventUpdate
from app.services import status_event_service

router = APIRouter(tags=["events"])


@router.post("/applications/{application_id}/events", response_model=StatusEventRead, status_code=201)
def create_event(application_id: int, data: StatusEventCreate, session: SessionDep):
    return status_event_service.create(session, application_id, data)


@router.patch("/events/{event_id}", response_model=StatusEventRead)
def update_event(event_id: int, data: StatusEventUpdate, session: SessionDep):
    return status_event_service.update(session, event_id, data)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, session: SessionDep):
    status_event_service.delete(session, event_id)
