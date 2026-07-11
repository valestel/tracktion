import json

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import SessionDep
from app.schemas.imports import ColumnMapping, ImportCommitResponse, ImportPreviewResponse, ImportRow
from app.services import import_service

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    session: SessionDep,
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
):
    file_bytes = await file.read()
    mapping = ColumnMapping.model_validate(json.loads(column_mapping))
    return import_service.preview(session, file_bytes, mapping)


@router.post("/commit", response_model=ImportCommitResponse)
def commit_import(rows: list[ImportRow], session: SessionDep):
    return import_service.commit(session, rows)
