"""client_requests.product_id

Revision ID: 20260512_0010
Revises: 20260512_0009
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0010"
down_revision: Union[str, None] = "20260512_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_requests",
        sa.Column("product_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_client_requests_product_id_products"),
        "client_requests",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_client_requests_product_id"),
        "client_requests",
        ["product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_client_requests_product_id"), table_name="client_requests")
    op.drop_constraint(
        op.f("fk_client_requests_product_id_products"),
        "client_requests",
        type_="foreignkey",
    )
    op.drop_column("client_requests", "product_id")
