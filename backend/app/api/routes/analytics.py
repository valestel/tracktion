from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.analytics import FunnelData, SankeyData, StatusEventRead
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/sankey", response_model=SankeyData)
def get_sankey(session: SessionDep):
    return analytics_service.get_sankey(session)


@router.get("/funnel", response_model=FunnelData)
def get_funnel(session: SessionDep):
    return analytics_service.get_funnel(session)


@router.get("/timeline/{application_id}", response_model=list[StatusEventRead])
def get_timeline(application_id: int, session: SessionDep):
    return analytics_service.get_timeline(session, application_id)
