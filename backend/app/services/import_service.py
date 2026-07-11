from sqlmodel import Session, and_, select

from app.core.csv_parser import parse_csv, normalize_date, normalize_status
from app.core.exceptions import ValidationError as AppValidationError
from app.core.status_log_parser import build_event_chain, parse_status_log
from app.core.validators import is_valid_link_or_email
from app.models.application import Application
from app.models.status import Status
from app.schemas.imports import ColumnMapping, ImportCommitResponse, ImportPreviewResponse, ImportRow
from app.services import application_service, company_service
from app.schemas.application import ApplicationCreate


def preview(
    session: Session, file_bytes: bytes, mapping: ColumnMapping
) -> ImportPreviewResponse:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[ImportRow] = []

    try:
        df = parse_csv(file_bytes)
    except Exception as exc:
        raise AppValidationError(f"Could not parse CSV: {exc}") from exc

    field_map = mapping.model_dump(exclude_none=True)
    required = {"company_name", "job_title", "application_date", "status"}
    missing = required - set(field_map.keys())
    if missing:
        raise AppValidationError(f"Missing required column mappings: {missing}")

    known_statuses = [s.name for s in session.exec(select(Status)).all()]
    # Imported applications always start their timeline at "applied" (if that
    # status exists), with later transitions layered on top.
    initial_status = normalize_status("applied", known_statuses)

    for i, raw in enumerate(df.to_dict(orient="records"), start=1):
        row_errors = []
        try:
            company_name = str(raw[field_map["company_name"]]).strip()
            company_description = (
                str(raw[field_map["company_description"]]).strip()
                if "company_description" in field_map
                else None
            )
            job_title = str(raw[field_map["job_title"]]).strip()
            date_val = normalize_date(str(raw[field_map["application_date"]]))
            status_val = normalize_status(str(raw[field_map["status"]]), known_statuses)
            link = str(raw[field_map["link"]]).strip() if "link" in field_map else None
            notes = str(raw[field_map["notes"]]).strip() if "notes" in field_map else None

            if not company_name:
                row_errors.append(f"Row {i}: company_name is empty")
            if not job_title:
                row_errors.append(f"Row {i}: job_title is empty")
            if date_val is None:
                row_errors.append(f"Row {i}: could not parse date '{raw[field_map['application_date']]}'")
            if status_val is None:
                row_errors.append(f"Row {i}: unknown status '{raw[field_map['status']]}'")
            if link and not is_valid_link_or_email(link):
                row_errors.append(f"Row {i}: invalid link/email '{link}'")

            if row_errors:
                errors.extend(row_errors)
                continue

            is_duplicate = _is_duplicate(session, company_name, job_title, date_val)  # type: ignore[arg-type]
            parsed_log = parse_status_log(notes, date_val, known_statuses)  # type: ignore[arg-type]
            for chunk in parsed_log.unrecognized:
                warnings.append(
                    f"Row {i} ({company_name}): log entry '{chunk}' does not match "
                    "any status and will stay in notes only"
                )
            status_events = build_event_chain(
                parsed_log.entries, status_val, date_val, initial_status  # type: ignore[arg-type]
            )
            rows.append(
                ImportRow(
                    company_name=company_name,
                    company_description=company_description if company_description else None,
                    job_title=job_title,
                    application_date=date_val,  # type: ignore[arg-type]
                    link=link if link else None,
                    status=status_val,  # type: ignore[arg-type]
                    notes=notes if notes else None,
                    is_duplicate=is_duplicate,
                    status_events=status_events,
                )
            )
        except KeyError as exc:
            errors.append(f"Row {i}: missing column {exc}")

    duplicate_count = sum(1 for r in rows if r.is_duplicate)
    return ImportPreviewResponse(
        rows=rows, errors=errors, warnings=warnings, duplicate_count=duplicate_count
    )


def commit(session: Session, rows: list[ImportRow]) -> ImportCommitResponse:
    created = 0
    skipped = 0
    for row in rows:
        if row.is_duplicate:
            skipped += 1
            continue
        company = company_service.get_or_create(session, row.company_name, row.company_description)
        data = ApplicationCreate(
            company_id=company.id,  # type: ignore[arg-type]
            job_title=row.job_title,
            application_date=row.application_date,
            link=row.link,
            status=row.status,
            notes=row.notes,
        )
        application_service.create(session, data, status_events=row.status_events)
        created += 1
    return ImportCommitResponse(created=created, skipped=skipped)


def _is_duplicate(session: Session, company_name: str, job_title: str, application_date) -> bool:
    from app.models.company import Company

    stmt = (
        select(Application)
        .join(Company)
        .where(
            and_(
                Company.name == company_name,
                Application.job_title == job_title,
                Application.application_date == application_date,
            )
        )
    )
    return session.exec(stmt).first() is not None
