"""lead_type in client_requests, service_requests table, approval fields in sales_materials

Revision ID: 20260512_0006
Revises: 20260512_0005
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0006"
down_revision: Union[str, None] = "20260512_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. client_requests.lead_type
    op.add_column(
        "client_requests",
        sa.Column(
            "lead_type",
            sa.String(length=32),
            nullable=False,
            server_default="request",
        ),
    )
    op.create_index(
        op.f("ix_client_requests_lead_type"),
        "client_requests",
        ["lead_type"],
        unique=False,
    )

    # 2. sales_materials approval fields
    op.add_column(
        "sales_materials",
        sa.Column(
            "approval_status",
            sa.String(length=32),
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column("sales_materials", sa.Column("approval_note", sa.Text(), nullable=True))
    op.add_column(
        "sales_materials",
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "sales_materials",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_sales_materials_approved_by_user_id_users"),
        "sales_materials",
        "users",
        ["approved_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_sales_materials_approval_status"),
        "sales_materials",
        ["approval_status"],
        unique=False,
    )

    # 3. service_requests
    op.create_table(
        "service_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("issue_type", sa.String(length=32), nullable=False),
        sa.Column("equipment", sa.String(length=256), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact_phone", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("assigned_dealer_id", sa.Integer(), nullable=True),
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
            ["user_id"],
            ["users.id"],
            name=op.f("fk_service_requests_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_dealer_id"],
            ["users.id"],
            name=op.f("fk_service_requests_assigned_dealer_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_requests")),
    )
    op.create_index(
        op.f("ix_service_requests_user_id"), "service_requests", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_service_requests_issue_type"),
        "service_requests",
        ["issue_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_requests_status"), "service_requests", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_service_requests_assigned_dealer_id"),
        "service_requests",
        ["assigned_dealer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_service_requests_assigned_dealer_id"), table_name="service_requests"
    )
    op.drop_index(op.f("ix_service_requests_status"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_issue_type"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_user_id"), table_name="service_requests")
    op.drop_table("service_requests")

    op.drop_index(
        op.f("ix_sales_materials_approval_status"), table_name="sales_materials"
    )
    op.drop_constraint(
        op.f("fk_sales_materials_approved_by_user_id_users"),
        "sales_materials",
        type_="foreignkey",
    )
    op.drop_column("sales_materials", "approved_at")
    op.drop_column("sales_materials", "approved_by_user_id")
    op.drop_column("sales_materials", "approval_note")
    op.drop_column("sales_materials", "approval_status")

    op.drop_index(op.f("ix_client_requests_lead_type"), table_name="client_requests")
    op.drop_column("client_requests", "lead_type")
