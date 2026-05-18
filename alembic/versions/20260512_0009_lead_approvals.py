"""lead_approvals table for HeadOfSales escalation

Revision ID: 20260512_0009
Revises: 20260512_0008
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0009"
down_revision: Union[str, None] = "20260512_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_approvals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("sales_user_id", sa.Integer(), nullable=False),
        sa.Column("proposed_dealer_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("decision_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["client_requests.id"],
            name=op.f("fk_lead_approvals_lead_id_client_requests"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sales_user_id"],
            ["users.id"],
            name=op.f("fk_lead_approvals_sales_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["proposed_dealer_id"],
            ["users.id"],
            name=op.f("fk_lead_approvals_proposed_dealer_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["decision_by_user_id"],
            ["users.id"],
            name=op.f("fk_lead_approvals_decision_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lead_approvals")),
    )
    op.create_index(
        op.f("ix_lead_approvals_lead_id"), "lead_approvals", ["lead_id"], unique=False
    )
    op.create_index(
        op.f("ix_lead_approvals_sales_user_id"),
        "lead_approvals",
        ["sales_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lead_approvals_status"), "lead_approvals", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_lead_approvals_status"), table_name="lead_approvals")
    op.drop_index(op.f("ix_lead_approvals_sales_user_id"), table_name="lead_approvals")
    op.drop_index(op.f("ix_lead_approvals_lead_id"), table_name="lead_approvals")
    op.drop_table("lead_approvals")
