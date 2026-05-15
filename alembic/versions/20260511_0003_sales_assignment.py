"""add assigned_sales_id to client_requests

Revision ID: 20260511_0003
Revises: 20260511_0002
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_0003"
down_revision: Union[str, None] = "20260511_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_requests",
        sa.Column("assigned_sales_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_client_requests_assigned_sales_id_users"),
        "client_requests",
        "users",
        ["assigned_sales_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_client_requests_assigned_sales_id"),
        "client_requests",
        ["assigned_sales_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_client_requests_assigned_sales_id"), table_name="client_requests"
    )
    op.drop_constraint(
        op.f("fk_client_requests_assigned_sales_id_users"),
        "client_requests",
        type_="foreignkey",
    )
    op.drop_column("client_requests", "assigned_sales_id")
