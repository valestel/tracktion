import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import create_app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app = create_app()

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_company(session: Session):
    from app.models.company import Company

    company = Company(name="Acme Corp", description="Test company")
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@pytest.fixture
def sample_application(session: Session, sample_company):
    from datetime import date

    from app.schemas.application import ApplicationCreate
    from app.services import application_service

    data = ApplicationCreate(
        company_id=sample_company.id,
        job_title="Software Engineer",
        application_date=date(2026, 1, 15),
        status="applied",
    )
    return application_service.create(session, data)
