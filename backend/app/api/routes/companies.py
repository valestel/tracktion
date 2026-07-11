from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(session: SessionDep):
    return company_service.list_all(session)


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(data: CompanyCreate, session: SessionDep):
    return company_service.create(session, data)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, session: SessionDep):
    return company_service.get(session, company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, data: CompanyUpdate, session: SessionDep):
    return company_service.update(session, company_id, data)
