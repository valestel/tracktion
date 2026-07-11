"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_STATUSES = [
    ("applied", "#60a5fa", 0),
    ("phone screen", "#a78bfa", 1),
    ("interview", "#f59e0b", 2),
    ("offer", "#4ade80", 3),
    ("rejected", "#f87171", 4),
    ("withdrawn", "#94a3b8", 5),
    ("waiting", "#e2e8f0", 6),
]


def upgrade() -> None:
    op.create_table(
        "company",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String, nullable=True),
    )
    op.create_index("ix_company_name", "company", ["name"])

    op.create_table(
        "application",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("company.id"), nullable=False),
        sa.Column("job_title", sa.String, nullable=False),
        sa.Column("application_date", sa.Date, nullable=False),
        sa.Column("link", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("notes", sa.String, nullable=True),
        sa.Column("archived_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_application_company_id", "application", ["company_id"])
    op.create_index("ix_application_status", "application", ["status"])
    op.create_index("ix_application_archived_at", "application", ["archived_at"])

    op.create_table(
        "status_event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("application_id", sa.Integer, sa.ForeignKey("application.id"), nullable=False),
        sa.Column("from_status", sa.String, nullable=True),
        sa.Column("to_status", sa.String, nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("note", sa.String, nullable=True),
    )
    op.create_index("ix_status_event_application_id", "status_event", ["application_id"])

    op.create_table(
        "status",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("color", sa.String, nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_status_name", "status", ["name"])

    # Seed default statuses
    op.bulk_insert(
        sa.table(
            "status",
            sa.column("name", sa.String),
            sa.column("color", sa.String),
            sa.column("sort_order", sa.Integer),
        ),
        [{"name": n, "color": c, "sort_order": o} for n, c, o in DEFAULT_STATUSES],
    )


def downgrade() -> None:
    op.drop_table("status_event")
    op.drop_table("application")
    op.drop_table("status")
    op.drop_table("company")
