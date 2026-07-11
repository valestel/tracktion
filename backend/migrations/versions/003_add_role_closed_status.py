"""Add role closed status

Revision ID: 003
Revises: 002
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

STATUS_NAME = "role closed"
STATUS_COLOR = "#64748b"


def upgrade() -> None:
    bind = op.get_bind()
    next_sort_order = bind.execute(sa.text("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM status")).scalar()
    op.bulk_insert(
        sa.table(
            "status",
            sa.column("name", sa.String),
            sa.column("color", sa.String),
            sa.column("sort_order", sa.Integer),
        ),
        [{"name": STATUS_NAME, "color": STATUS_COLOR, "sort_order": next_sort_order}],
    )


def downgrade() -> None:
    status_table = sa.table("status", sa.column("name", sa.String))
    op.execute(status_table.delete().where(status_table.c.name == STATUS_NAME))
