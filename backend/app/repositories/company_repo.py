from typing import Optional

from sqlmodel import Session, select

from app.models.company import Company


def get(session: Session, company_id: int) -> Optional[Company]:
    return session.get(Company, company_id)


def get_by_name(session: Session, name: str) -> Optional[Company]:
    return session.exec(select(Company).where(Company.name == name)).first()


def list_all(session: Session) -> list[Company]:
    return list(session.exec(select(Company)).all())


def create(session: Session, company: Company) -> Company:
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def update(session: Session, company: Company) -> Company:
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def delete(session: Session, company_id: int) -> bool:
    company = session.get(Company, company_id)
    if not company:
        return False
    session.delete(company)
    session.commit()
    return True
