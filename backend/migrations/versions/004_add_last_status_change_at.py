"""Add last_status_change_at to application

Revision ID: 004
Revises: 003
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "application", sa.Column("last_status_change_at", sa.DateTime, nullable=True)
    )

    bind = op.get_bind()
    # Only real transitions count as a "status change" — exclude the initial
    # None -> status event written at creation, so an application that has
    # never had its status changed correctly backfills to NULL (its recency
    # is then driven solely by application_date on the frontend).
    bind.execute(
        sa.text(
            """
            UPDATE application
            SET last_status_change_at = (
                SELECT MAX(timestamp) FROM status_event
                WHERE status_event.application_id = application.id
                AND status_event.from_status IS NOT NULL
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("application", "last_status_change_at")
