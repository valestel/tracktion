from sqlmodel import Session

from app.models.company import Company
from app.repositories import company_repo
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.core.exceptions import ConflictError, NotFoundError, ValidationError


def get(session: Session, company_id: int) -> CompanyRead:
    company = company_repo.get(session, company_id)
    if not company:
        raise NotFoundError(company_id)
    return CompanyRead.model_validate(company)


def list_all(session: Session) -> list[CompanyRead]:
    return [CompanyRead.model_validate(c) for c in company_repo.list_all(session)]


def create(session: Session, data: CompanyCreate) -> CompanyRead:
    company = Company(**data.model_dump())
    return CompanyRead.model_validate(company_repo.create(session, company))


def update(session: Session, company_id: int, data: CompanyUpdate) -> CompanyRead:
    company = company_repo.get(session, company_id)
    if not company:
        raise NotFoundError(company_id)

    updates = data.model_dump(exclude_unset=True)

    if "name" in updates:
        new_name = updates["name"].strip()
        if not new_name:
            raise ValidationError("Company name cannot be empty")
        updates["name"] = new_name

        if new_name != company.name:
            existing = company_repo.get_by_name(session, new_name)
            if existing and existing.id != company.id:
                raise ConflictError(f"A company named '{new_name}' already exists")

    for field, value in updates.items():
        setattr(company, field, value)
    return CompanyRead.model_validate(company_repo.update(session, company))


def get_or_create(session: Session, name: str, description: str | None = None) -> Company:
    company = company_repo.get_by_name(session, name)
    if company:
        if description and not company.description:
            company.description = description
            return company_repo.update(session, company)
        return company
    company = Company(name=name, description=description)
    return company_repo.create(session, company)
