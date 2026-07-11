import pytest
from sqlmodel import Session

from app.core.exceptions import ValidationError as AppValidationError
from app.models.status import Status
from app.schemas.imports import ColumnMapping
from app.services import import_service
from datetime import date, datetime


def _seed_statuses(session: Session):
    for name in ("applied", "interview", "rejected"):
        session.add(Status(name=name, color=None, sort_order=0))
    session.commit()


MAPPING = ColumnMapping(
    company_name="Company",
    job_title="Title",
    application_date="Date",
    status="Status",
)

VALID_CSV = b"Company,Title,Date,Status\nAcme,Engineer,2026-01-01,applied\nBeta,Designer,2026-02-15,interview\n"


def test_preview_parses_valid_csv(session: Session):
    _seed_statuses(session)
    result = import_service.preview(session, VALID_CSV, MAPPING)
    assert len(result.rows) == 2
    assert result.errors == []
    assert result.duplicate_count == 0


def test_preview_marks_duplicates(session: Session):
    _seed_statuses(session)
    # First preview + commit to create a duplicate
    preview = import_service.preview(session, VALID_CSV, MAPPING)
    import_service.commit(session, preview.rows)

    # Preview again — both rows should be duplicates
    result = import_service.preview(session, VALID_CSV, MAPPING)
    assert result.duplicate_count == 2
    assert all(r.is_duplicate for r in result.rows)


def test_preview_reports_malformed_date(session: Session):
    _seed_statuses(session)
    csv_bytes = b"Company,Title,Date,Status\nAcme,Engineer,not-a-date,applied\n"
    result = import_service.preview(session, csv_bytes, MAPPING)
    assert len(result.errors) == 1
    assert "date" in result.errors[0].lower()


def test_preview_reports_missing_mapping():
    # Mapping without required fields raises ValidationError
    with pytest.raises(AppValidationError):
        import_service.preview(None, VALID_CSV, ColumnMapping())  # type: ignore[arg-type]


def test_commit_skips_duplicates(session: Session):
    _seed_statuses(session)
    preview = import_service.preview(session, VALID_CSV, MAPPING)
    result1 = import_service.commit(session, preview.rows)
    assert result1.created == 2
    assert result1.skipped == 0

    preview2 = import_service.preview(session, VALID_CSV, MAPPING)
    result2 = import_service.commit(session, preview2.rows)
    assert result2.created == 0
    assert result2.skipped == 2


def test_commit_creates_status_events(session: Session):
    from sqlmodel import select
    from app.models.status_event import StatusEvent

    _seed_statuses(session)
    preview = import_service.preview(session, VALID_CSV, MAPPING)
    import_service.commit(session, preview.rows)

    events = session.exec(select(StatusEvent)).all()
    # row 1 (applied): 1 event; row 2 (interview): applied -> interview = 2 events
    assert len(events) == 3


LINK_MAPPING = ColumnMapping(
    company_name="Company",
    job_title="Title",
    application_date="Date",
    status="Status",
    link="Link",
)


def test_preview_reports_invalid_link(session: Session):
    _seed_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Link\n"
        b"Acme,Engineer,2026-01-01,applied,not-a-valid-link\n"
    )
    result = import_service.preview(session, csv_bytes, LINK_MAPPING)
    assert len(result.errors) == 1
    assert "link" in result.errors[0].lower()
    assert result.rows == []


def test_preview_accepts_valid_email_link(session: Session):
    _seed_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Link\n"
        b"Acme,Engineer,2026-01-01,applied,jobs@example-company.com\n"
    )
    result = import_service.preview(session, csv_bytes, LINK_MAPPING)
    assert result.errors == []
    assert result.rows[0].link == "jobs@example-company.com"


def _seed_log_statuses(session: Session):
    for name in ("applied", "screening call", "tech interview", "offer", "rejected"):
        session.add(Status(name=name, color=None, sort_order=0))
    session.commit()


NOTES_MAPPING = ColumnMapping(
    company_name="Company",
    job_title="Title",
    application_date="Date",
    status="Status",
    notes="Notes",
)


def test_preview_parses_status_log_into_events(session: Session):
    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'Acme,Engineer,2026-01-05,tech interview,"4.06 - screening call, 12.06 - tech interview"\n'
    )
    result = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    assert result.errors == []
    events = result.rows[0].status_events
    assert len(events) == 3
    assert events[0].from_status is None
    assert events[0].to_status == "applied"
    assert events[0].timestamp.date() == date(2026, 1, 5)
    assert events[1].from_status == "applied"
    assert events[1].to_status == "screening call"
    assert events[1].timestamp.date() == date(2026, 6, 4)
    assert events[2].from_status == "screening call"
    assert events[2].to_status == "tech interview"


def test_preview_year_less_date_uses_application_date_year(session: Session):
    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'Acme,Engineer,2025-01-05,screening call,"4.06 - screening call"\n'
    )
    result = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    events = result.rows[0].status_events
    assert events[1].to_status == "screening call"
    assert events[1].timestamp.year == 2025


def test_preview_skips_unknown_status_in_log(session: Session):
    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'Acme,Engineer,2026-01-05,offer,"4.06 - some made up status, 12.06 - offer"\n'
    )
    result = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    assert result.errors == []
    events = result.rows[0].status_events
    assert len(events) == 2
    assert events[0].to_status == "applied"
    assert events[1].to_status == "offer"
    assert events[1].timestamp.date() == date(2026, 6, 12)


def test_preview_notes_with_zero_matches_starts_timeline_at_applied(session: Session):
    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'Acme,Engineer,2026-01-05,applied,"just some free text notes"\n'
    )
    result = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    events = result.rows[0].status_events
    assert len(events) == 1
    assert events[0].from_status is None
    assert events[0].to_status == "applied"
    assert events[0].timestamp.date() == date(2026, 1, 5)


def test_preview_non_applied_status_without_log_gets_catchup_event(session: Session):
    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b"Acme,Engineer,2026-01-05,rejected,\n"
    )
    result = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    events = result.rows[0].status_events
    assert len(events) == 2
    assert events[0].to_status == "applied"
    assert events[0].timestamp.date() == date(2026, 1, 5)
    assert events[1].from_status == "applied"
    assert events[1].to_status == "rejected"


def test_commit_creates_status_event_chain_with_derived_timestamps(session: Session):
    from sqlmodel import select
    from app.models.status_event import StatusEvent

    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'Acme,Engineer,2026-01-05,offer,"4.06 - screening call, 12.06 - tech interview"\n'
    )
    preview = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    import_service.commit(session, preview.rows)

    events = session.exec(select(StatusEvent)).all()
    # applied -> screening call -> tech interview -> offer (catch-up)
    assert len(events) == 4
    by_to = {e.to_status: e for e in events}
    assert by_to["applied"].from_status is None
    assert by_to["applied"].timestamp.date() == date(2026, 1, 5)
    assert by_to["screening call"].from_status == "applied"
    assert by_to["screening call"].timestamp.date() == date(2026, 6, 4)
    assert by_to["tech interview"].from_status == "screening call"
    assert by_to["tech interview"].timestamp.date() == date(2026, 6, 12)
    assert by_to["offer"].from_status == "tech interview"
    # catch-up event timestamp should be close to "now", not a parsed log date
    assert by_to["offer"].timestamp.date() == datetime.utcnow().date()


def test_commit_chain_matching_final_status_does_not_double_create(session: Session):
    from sqlmodel import select
    from app.models.status_event import StatusEvent

    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'Acme,Engineer,2026-01-05,tech interview,"4.06 - screening call, 12.06 - tech interview"\n'
    )
    preview = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    import_service.commit(session, preview.rows)

    events = session.exec(select(StatusEvent)).all()
    assert len(events) == 3


DESCRIPTION_MAPPING = ColumnMapping(
    company_name="Company",
    company_description="Description",
    job_title="Title",
    application_date="Date",
    status="Status",
)


def test_commit_imports_company_description(session: Session):
    from app.models.company import Company
    from sqlmodel import select

    _seed_statuses(session)
    csv_bytes = (
        b"Company,Description,Title,Date,Status\n"
        b"Acme,AI for accounts payable,Engineer,2026-01-01,applied\n"
    )
    preview = import_service.preview(session, csv_bytes, DESCRIPTION_MAPPING)
    assert preview.rows[0].company_description == "AI for accounts payable"
    import_service.commit(session, preview.rows)

    company = session.exec(select(Company).where(Company.name == "Acme")).first()
    assert company is not None
    assert company.description == "AI for accounts payable"


def test_preview_parses_dates_day_first(session: Session):
    _seed_statuses(session)
    csv_bytes = b"Company,Title,Date,Status\nAcme,Engineer,09/07/2026,applied\n"
    result = import_service.preview(session, csv_bytes, MAPPING)
    assert result.errors == []
    assert result.rows[0].application_date == date(2026, 7, 9)


def test_preview_warns_about_unrecognized_log_entries(session: Session):
    _seed_log_statuses(session)
    csv_bytes = (
        b"Company,Title,Date,Status,Notes\n"
        b'MNI,Engineer,2026-06-26,rejected,"26.06 - intro call with recruiter\n6.07 - rejected"\n'
    )
    result = import_service.preview(session, csv_bytes, NOTES_MAPPING)
    assert result.errors == []
    assert len(result.warnings) == 1
    assert "intro call with recruiter" in result.warnings[0]
    assert "MNI" in result.warnings[0]
    # the recognized entry still becomes an event
    events = result.rows[0].status_events
    assert [e.to_status for e in events] == ["applied", "rejected"]


def test_preview_handles_utf8_bom_in_header(session: Session):
    _seed_statuses(session)
    csv_bytes = b"\xef\xbb\xbfCompany,Title,Date,Status\nAcme,Engineer,2026-01-01,applied\n"
    result = import_service.preview(session, csv_bytes, MAPPING)
    assert result.errors == []
    assert result.rows[0].company_name == "Acme"
