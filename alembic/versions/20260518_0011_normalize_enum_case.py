"""normalize enum columns to lowercase (StrEnum values)

Revision ID: 20260518_0011
Revises: 20260512_0010
Create Date: 2026-05-18

SQLAlchemy Enum по умолчанию писал в БД UPPERCASE (member.name), а миграции
ставили server_default lowercase (member.value). Чтобы единственный источник
правды был — value (StrEnum), в моделях добавлен values_callable, а старые
записи нормализуются этим скриптом: LOWER() по всем enum-колонкам.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260518_0011"
down_revision: Union[str, None] = "20260512_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Все enum-колонки в проекте: (table, column).
ENUM_COLUMNS: list[tuple[str, str]] = [
    ("users", "role"),
    ("client_requests", "lead_type"),
    ("client_requests", "status"),
    ("service_requests", "issue_type"),
    ("service_requests", "status"),
    ("lead_approvals", "status"),
    ("sales_materials", "category"),
    ("sales_materials", "file_type"),
    ("sales_materials", "approval_status"),
    ("content_items", "type"),
    ("content_items", "file_type"),
    ("content_items", "status"),
    ("broadcasts", "file_type"),
    ("broadcasts", "target_role"),
    ("broadcasts", "status"),
]


def upgrade() -> None:
    for table, column in ENUM_COLUMNS:
        op.execute(
            f"UPDATE {table} SET {column} = LOWER({column}) "
            f"WHERE {column} IS NOT NULL AND {column} <> LOWER({column})"
        )


def downgrade() -> None:
    # Обратная конвертация в UPPERCASE не нужна (модели всё равно ожидают lowercase).
    pass
