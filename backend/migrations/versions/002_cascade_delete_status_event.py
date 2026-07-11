"""Cascade delete status_event on application delete

Revision ID: 002
Revises: 001
Create Date: 2026-07-06
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


NAMING_CONVENTION = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}
FK_NAME = "fk_status_event_application_id_application"


def upgrade() -> None:
    with op.batch_alter_table("status_event", naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint(FK_NAME, type_="foreignkey")
        batch_op.create_foreign_key(
            FK_NAME,
            "application",
            ["application_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("status_event", naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint(FK_NAME, type_="foreignkey")
        batch_op.create_foreign_key(
            FK_NAME,
            "application",
            ["application_id"],
            ["id"],
        )
