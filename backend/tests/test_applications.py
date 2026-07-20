from datetime import date

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlmodel import Session, select

from app.models.application import Application
from app.models.company import Company
from app.models.status_event import StatusEvent
from app.schemas.application import ApplicationCreate, ApplicationUpdate, BulkDelete, BulkUpdate
from app.services import application_service
from app.core.exceptions import NotFoundError


def test_create_writes_initial_status_event(session: Session, sample_company):
    data = ApplicationCreate(
        company_id=sample_company.id,
        job_title="Backend Engineer",
        application_date=date(2026, 2, 1),
        status="applied",
    )
    app = application_service.create(session, data)

    events = session.exec(
        select(StatusEvent).where(StatusEvent.application_id == app.id)
    ).all()
    assert len(events) == 1
    assert events[0].from_status is None
    assert events[0].to_status == "applied"


def test_update_status_writes_status_event(session: Session, sample_application):
    application_service.update(
        session, sample_application.id, ApplicationUpdate(status="interview")
    )
    events = session.exec(
        select(StatusEvent).where(StatusEvent.application_id == sample_application.id)
    ).all()
    assert len(events) == 2
    assert events[-1].from_status == "applied"
    assert events[-1].to_status == "interview"


def test_update_no_status_change_writes_no_event(session: Session, sample_application):
    application_service.update(
        session, sample_application.id, ApplicationUpdate(notes="Updated notes")
    )
    events = session.exec(
        select(StatusEvent).where(StatusEvent.application_id == sample_application.id)
    ).all()
    assert len(events) == 1  # only the initial creation event


def test_list_all_sorted_by_application_date_descending(session: Session, sample_company):
    # created in a shuffled order, like rows arriving from a CSV import
    for d in (date(2026, 7, 3), date(2026, 7, 9), date(2026, 6, 26), date(2026, 7, 7)):
        application_service.create(
            session,
            ApplicationCreate(
                company_id=sample_company.id,
                job_title=f"Role {d}",
                application_date=d,
                status="applied",
            ),
        )

    apps = application_service.list_all(session)
    dates = [a.application_date for a in apps]
    assert dates == sorted(dates, reverse=True)


def test_bulk_update_writes_status_events(session: Session, sample_company):
    apps = []
    for i in range(3):
        data = ApplicationCreate(
            company_id=sample_company.id,
            job_title=f"Role {i}",
            application_date=date(2026, 3, i + 1),
            status="applied",
        )
        apps.append(application_service.create(session, data))

    ids = [a.id for a in apps]
    application_service.bulk_update(session, BulkUpdate(ids=ids, status="interview"))

    for app in apps:
        events = session.exec(
            select(StatusEvent).where(StatusEvent.application_id == app.id)
        ).all()
        assert len(events) == 2
        assert events[-1].to_status == "interview"


def test_bulk_delete_removes_applications_and_status_events(session: Session, sample_company):
    apps = []
    for i in range(3):
        data = ApplicationCreate(
            company_id=sample_company.id,
            job_title=f"Role {i}",
            application_date=date(2026, 3, i + 1),
            status="applied",
        )
        apps.append(application_service.create(session, data))

    ids = [a.id for a in apps]
    application_service.bulk_delete(session, BulkDelete(ids=ids))

    assert session.exec(select(Application)).all() == []
    assert session.exec(select(StatusEvent)).all() == []


def test_bulk_delete_removes_orphaned_company(session: Session, sample_application, sample_company):
    application_service.bulk_delete(session, BulkDelete(ids=[sample_application.id]))
    assert session.get(Company, sample_company.id) is None


def test_bulk_delete_keeps_company_with_remaining_applications(
    session: Session, sample_application, sample_company
):
    other = application_service.create(
        session,
        ApplicationCreate(
            company_id=sample_company.id,
            job_title="Data Engineer",
            application_date=date(2026, 2, 10),
            status="applied",
        ),
    )
    application_service.bulk_delete(session, BulkDelete(ids=[sample_application.id]))

    assert session.get(Company, sample_company.id) is not None
    assert session.get(Application, other.id) is not None


def test_archive_sets_archived_at(session: Session, sample_application):
    archived = application_service.archive(session, sample_application.id)
    assert archived.archived_at is not None


def test_unarchive_clears_archived_at(session: Session, sample_application):
    application_service.archive(session, sample_application.id)
    unarchived = application_service.unarchive(session, sample_application.id)
    assert unarchived.archived_at is None


def test_archived_excluded_from_default_list(session: Session, sample_application):
    application_service.archive(session, sample_application.id)
    apps = application_service.list_all(session)
    assert all(a.id != sample_application.id for a in apps)


def test_ever_status_includes_apps_that_moved_on(session: Session, sample_application):
    application_service.update(
        session, sample_application.id, ApplicationUpdate(status="take-home task")
    )
    application_service.update(
        session, sample_application.id, ApplicationUpdate(status="rejected")
    )

    apps = application_service.list_all(session, ever_status=["take-home task"])
    assert any(a.id == sample_application.id for a in apps)
    assert all(a.status != "take-home task" for a in apps)


def test_ever_status_excludes_apps_that_never_had_it(session: Session, sample_application):
    apps = application_service.list_all(session, ever_status=["take-home task"])
    assert all(a.id != sample_application.id for a in apps)


def test_ever_status_match_all_requires_every_selected_status(
    session: Session, sample_company
):
    data = ApplicationCreate(
        company_id=sample_company.id,
        job_title="Only take-home",
        application_date=date(2026, 3, 1),
        status="applied",
    )
    only_take_home = application_service.create(session, data)
    application_service.update(
        session, only_take_home.id, ApplicationUpdate(status="take-home task")
    )

    data = ApplicationCreate(
        company_id=sample_company.id,
        job_title="Both statuses",
        application_date=date(2026, 3, 2),
        status="applied",
    )
    both = application_service.create(session, data)
    application_service.update(session, both.id, ApplicationUpdate(status="take-home task"))
    application_service.update(session, both.id, ApplicationUpdate(status="offer"))

    apps = application_service.list_all(
        session,
        ever_status=["take-home task", "offer"],
        ever_status_match_all=True,
    )
    ids = {a.id for a in apps}
    assert both.id in ids
    assert only_take_home.id not in ids


def test_get_nonexistent_raises_not_found(session: Session):
    with pytest.raises(NotFoundError):
        application_service.get(session, 99999)


def test_application_create_accepts_valid_url_link():
    data = ApplicationCreate(
        company_id=1,
        job_title="Engineer",
        application_date=date(2026, 4, 1),
        status="applied",
        link="https://example.com/careers/123",
    )
    assert data.link == "https://example.com/careers/123"


def test_application_create_accepts_valid_email_link():
    data = ApplicationCreate(
        company_id=1,
        job_title="Engineer",
        application_date=date(2026, 4, 1),
        status="applied",
        link="jobs@example-company.com",
    )
    assert data.link == "jobs@example-company.com"


def test_application_create_allows_empty_link():
    data = ApplicationCreate(
        company_id=1,
        job_title="Engineer",
        application_date=date(2026, 4, 1),
        status="applied",
    )
    assert data.link is None


def test_application_create_rejects_invalid_link():
    with pytest.raises(PydanticValidationError):
        ApplicationCreate(
            company_id=1,
            job_title="Engineer",
            application_date=date(2026, 4, 1),
            status="applied",
            link="not-a-valid-link",
        )


def test_application_update_rejects_invalid_link():
    # The original bug report: a bare email/domain fragment with no scheme,
    # which the frontend would otherwise resolve relative to its own origin.
    with pytest.raises(PydanticValidationError):
        ApplicationUpdate(link="localhost:8000/jobs@example-company.com")
