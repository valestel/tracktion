from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    BulkDelete,
    BulkUpdate,
)
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    session: SessionDep,
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    include_archived: bool = False,
    ever_status: Optional[list[str]] = Query(None),
    ever_status_match_all: bool = False,
):
    return application_service.list_all(
        session,
        include_archived=include_archived,
        company_id=company_id,
        status=status,
        ever_status=ever_status,
        ever_status_match_all=ever_status_match_all,
    )


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(data: ApplicationCreate, session: SessionDep):
    return application_service.create(session, data)


@router.get("/{app_id}", response_model=ApplicationRead)
def get_application(app_id: int, session: SessionDep):
    return application_service.get(session, app_id)


@router.patch("/bulk", response_model=list[ApplicationRead])
def bulk_update_applications(data: BulkUpdate, session: SessionDep):
    return application_service.bulk_update(session, data)


@router.post("/bulk-delete", status_code=204)
def bulk_delete_applications(data: BulkDelete, session: SessionDep):
    application_service.bulk_delete(session, data)


@router.patch("/{app_id}", response_model=ApplicationRead)
def update_application(app_id: int, data: ApplicationUpdate, session: SessionDep):
    return application_service.update(session, app_id, data)


@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, session: SessionDep):
    application_service.delete(session, app_id)


@router.post("/{app_id}/archive", response_model=ApplicationRead)
def archive_application(app_id: int, session: SessionDep):
    return application_service.archive(session, app_id)


@router.post("/{app_id}/unarchive", response_model=ApplicationRead)
def unarchive_application(app_id: int, session: SessionDep):
    return application_service.unarchive(session, app_id)
