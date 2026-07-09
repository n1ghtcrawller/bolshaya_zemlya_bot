"""bitrix_outbox table for guaranteed lead delivery to Bitrix24

Revision ID: 20260602_0012
Revises: 20260518_0011
Create Date: 2026-06-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0012"
down_revision: Union[str, None] = "20260518_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bitrix_outbox",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="pending"
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("bitrix_lead_id", sa.Integer(), nullable=True),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bitrix_outbox")),
    )
    op.create_index(
        op.f("ix_bitrix_outbox_source_id"), "bitrix_outbox", ["source_id"], unique=False
    )
    op.create_index(
        op.f("ix_bitrix_outbox_status"), "bitrix_outbox", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_bitrix_outbox_next_attempt_at"),
        "bitrix_outbox",
        ["next_attempt_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_bitrix_outbox_next_attempt_at"), table_name="bitrix_outbox")
    op.drop_index(op.f("ix_bitrix_outbox_status"), table_name="bitrix_outbox")
    op.drop_index(op.f("ix_bitrix_outbox_source_id"), table_name="bitrix_outbox")
    op.drop_table("bitrix_outbox")
