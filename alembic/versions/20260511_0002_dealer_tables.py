"""dealer tables: dealer_profiles, sales_materials

Revision ID: 20260511_0002
Revises: 20260511_0001
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_0002"
down_revision: Union[str, None] = "20260511_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dealer_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("company", sa.String(length=256), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
            name=op.f("fk_dealer_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dealer_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_dealer_profiles_user_id")),
    )

    op.create_table(
        "sales_materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=512), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
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
            ["uploaded_by_user_id"],
            ["users.id"],
            name=op.f("fk_sales_materials_uploaded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_materials")),
    )
    op.create_index(
        op.f("ix_sales_materials_category"), "sales_materials", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_sales_materials_is_active"), "sales_materials", ["is_active"], unique=False
    )

    op.create_index(
        op.f("ix_client_requests_assigned_dealer_id"),
        "client_requests",
        ["assigned_dealer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_client_requests_assigned_dealer_id"), table_name="client_requests"
    )
    op.drop_index(op.f("ix_sales_materials_is_active"), table_name="sales_materials")
    op.drop_index(op.f("ix_sales_materials_category"), table_name="sales_materials")
    op.drop_table("sales_materials")
    op.drop_table("dealer_profiles")
