from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum as SAEnum, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def lower_enum(enum_cls: type[PyEnum], *, name: str, length: int = 32) -> SAEnum:
    """SQLAlchemy Enum, который хранит/читает member.value, а не member.name.

    Для StrEnum-классов с lowercase-значениями (наш кейс): в БД и server_default
    лежит `client`/`dealer`/..., а Python-сторона мапит их обратно в члены enum.
    Без этого SQLAlchemy по дефолту использует имена ('CLIENT'), что не сходится
    с миграциями и SQL-апдейтами.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        length=length,
        values_callable=lambda obj: [e.value for e in obj],
    )
