"""content_items: media + approval fields

Revision ID: 20260512_0008
Revises: 20260512_0007
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0008"
down_revision: Union[str, None] = "20260512_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_items", sa.Column("file_type", sa.String(length=32), nullable=True))
    op.add_column(
        "content_items", sa.Column("telegram_file_id", sa.String(length=512), nullable=True)
    )
    op.add_column("content_items", sa.Column("approval_note", sa.Text(), nullable=True))
    op.add_column(
        "content_items", sa.Column("approved_by_user_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "content_items",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_content_items_approved_by_user_id_users"),
        "content_items",
        "users",
        ["approved_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_content_items_approved_by_user_id_users"),
        "content_items",
        type_="foreignkey",
    )
    op.drop_column("content_items", "approved_at")
    op.drop_column("content_items", "approved_by_user_id")
    op.drop_column("content_items", "approval_note")
    op.drop_column("content_items", "telegram_file_id")
    op.drop_column("content_items", "file_type")
