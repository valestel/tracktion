"""Wipe the database, or populate it with sample data, for local development.

Usage:
    cd backend && uv run python scripts/seed_db.py wipe [-y]
    cd backend && uv run python scripts/seed_db.py seed

Pass -y/--yes to skip the confirmation prompt on `wipe`.
"""

import argparse
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
# app.config.settings.db_path is relative and assumed relative to backend/
# (the same assumption app.main makes when run via `cd backend && uvicorn ...`).
# Normalize cwd here so this script resolves the same db regardless of where
# it's invoked from.
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session, delete, select  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import engine, init_db  # noqa: E402
from app.models import Application, Company, Status, StatusEvent  # noqa: E402

RNG_SEED = 42

COMPANIES = [
    ("Acme Corp", "Cloud infrastructure tooling"),
    ("Globex Corporation", "Fintech payments platform"),
    ("Initech", "Enterprise B2B SaaS"),
    ("Umbrella Corp", "Health-tech and biotech data systems"),
    ("Stark Industries", "Consumer hardware and robotics"),
    ("Wayne Enterprises", "Applied AI and security research"),
    ("Hooli", "Search and ads infrastructure"),
    ("Wonka Industries", "E-commerce and logistics"),
    ("Pied Piper", "Distributed storage and compression"),
    ("Soylent Corp", "Developer tools startup"),
]

JOB_TITLES = [
    "Software Engineer",
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Data Engineer",
    "Site Reliability Engineer",
    "Product Engineer",
    "Mobile Engineer",
    "Machine Learning Engineer",
]

# Each path is a sequence of statuses the application moves through over time.
STATUS_PATHS = [
    ["applied", "ghosted"],
    ["applied", "screen/intro", "rejected"],
    ["applied", "screen/intro", "tech interview", "rejected"],
    ["applied", "screen/intro", "tech interview", "offer"],
    ["applied", "take-home task", "tech interview", "culture interview", "offer"],
    ["applied", "take-home task", "rejected"],
    ["applied", "withdrawn"],
    ["applied", "waiting"],
    ["applied", "screen/intro", "waiting"],
    ["applied", "screen/intro", "tech interview", "culture interview", "rejected"],
]

ARCHIVABLE_TERMINAL_STATUSES = {"rejected", "withdrawn", "ghosted", "offer"}

NOTE_SNIPPETS = [
    "Found via referral from a former colleague.",
    "Applied through the company careers page.",
    "Recruiter reached out on LinkedIn.",
    "Role looked like a strong fit for my background.",
    "Salary range wasn't listed, need to ask.",
    "Team seems small, reports directly to the CTO.",
    "Followed up after two weeks of silence.",
    None,
    None,
]


def wipe_data(session: Session) -> None:
    session.exec(delete(StatusEvent))
    session.exec(delete(Application))
    session.exec(delete(Company))
    session.exec(delete(Status))
    session.commit()


def seed_statuses(session: Session) -> None:
    existing_names = {s.name for s in session.exec(select(Status)).all()}
    for name, color, sort_order in settings.default_statuses:
        if name not in existing_names:
            session.add(Status(name=name, color=color, sort_order=sort_order))
    session.commit()


def seed_companies(session: Session) -> list[Company]:
    existing = {c.name: c for c in session.exec(select(Company)).all()}
    companies = []
    for name, desc in COMPANIES:
        company = existing.get(name)
        if not company:
            company = Company(name=name, description=desc)
            session.add(company)
        companies.append(company)
    session.commit()
    for c in companies:
        session.refresh(c)
    return companies


def seed_applications(session: Session, companies: list[Company], rng: random.Random) -> None:
    now = datetime.utcnow()

    for i in range(24):
        company = rng.choice(companies)
        job_title = rng.choice(JOB_TITLES)
        path = rng.choice(STATUS_PATHS)
        application_date = now - timedelta(days=rng.randint(2, 25))

        # Spread status transitions out between application_date and now (or a bit after).
        num_steps = len(path)
        step_gap_days = max(1, rng.randint(2, 10))
        timestamps = [application_date + timedelta(days=step_gap_days * idx) for idx in range(num_steps)]
        # Don't let events land in the future.
        timestamps = [min(t, now) for t in timestamps]

        app = Application(
            company_id=company.id,
            job_title=job_title,
            application_date=application_date.date(),
            link=f"https://dummyexample-{company.name.lower().replace(' ', '')}.com/careers/{i}" if rng.random() > 0.3 else None,
            status=path[0],
            notes=rng.choice(NOTE_SNIPPETS),
            created_at=timestamps[0],
            updated_at=timestamps[-1],
            last_status_change_at=timestamps[0] if num_steps == 1 else timestamps[-1],
        )
        session.add(app)
        session.flush()  # assign app.id

        session.add(
            StatusEvent(
                application_id=app.id,
                from_status=None,
                to_status=path[0],
                timestamp=timestamps[0],
            )
        )
        for idx in range(1, num_steps):
            session.add(
                StatusEvent(
                    application_id=app.id,
                    from_status=path[idx - 1],
                    to_status=path[idx],
                    timestamp=timestamps[idx],
                )
            )
            app.status = path[idx]

        if app.status in ARCHIVABLE_TERMINAL_STATUSES and rng.random() > 0.4:
            app.archived_at = timestamps[-1] + timedelta(days=1)

        session.add(app)

    session.commit()


def run_wipe(args: argparse.Namespace) -> None:
    db_path = Path(settings.db_path).resolve()
    if not args.yes:
        answer = input(f"This will DELETE ALL DATA in {db_path}. Continue? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return

    init_db()
    with Session(engine) as session:
        wipe_data(session)

    print(f"Wiped all data from {db_path}.")


def run_seed(_args: argparse.Namespace) -> None:
    db_path = Path(settings.db_path).resolve()
    init_db()
    rng = random.Random(RNG_SEED)

    with Session(engine) as session:
        seed_statuses(session)
        companies = seed_companies(session)
        seed_applications(session, companies, rng)

    print(f"Seeded {db_path} with {len(COMPANIES)} companies and 24 applications.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    wipe_parser = subparsers.add_parser("wipe", help="delete all data from the database")
    wipe_parser.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompt")
    wipe_parser.set_defaults(func=run_wipe)

    seed_parser = subparsers.add_parser("seed", help="populate the database with sample data")
    seed_parser.set_defaults(func=run_seed)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
