"""dealer specialization

Revision ID: 20260512_0007
Revises: 20260512_0006
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0007"
down_revision: Union[str, None] = "20260512_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "dealer_profiles",
        sa.Column("specialization", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("dealer_profiles", "specialization")
