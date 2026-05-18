from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import UserRole
from bot.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self._session.scalar(stmt)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def list_by_role(
        self, role: UserRole, *, limit: int = 50, offset: int = 0
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .where(User.role == role, User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_role(self) -> dict[UserRole, int]:
        stmt = (
            select(User.role, func.count())
            .where(User.is_active.is_(True))
            .group_by(User.role)
        )
        rows = await self._session.execute(stmt)
        return {role: int(count) for role, count in rows.all()}

    async def list_telegram_ids_by_role(
        self, role: UserRole | None = None
    ) -> Sequence[int]:
        stmt = select(User.telegram_id).where(User.is_active.is_(True))
        if role is not None:
            stmt = stmt.where(User.role == role)
        return (await self._session.scalars(stmt)).all()

    async def has_role(self, role: UserRole) -> bool:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.role == role, User.is_active.is_(True))
        )
        return int(await self._session.scalar(stmt) or 0) > 0

    async def create(
        self,
        *,
        telegram_id: int,
        full_name: str,
        username: str | None,
        language_code: str | None,
        role: UserRole = UserRole.CLIENT,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            language_code=language_code,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_profile_fields(
        self,
        user: User,
        *,
        full_name: str | None = None,
        username: str | None = None,
        language_code: str | None = None,
    ) -> User:
        if full_name is not None:
            user.full_name = full_name
        if username is not None:
            user.username = username
        if language_code is not None:
            user.language_code = language_code
        await self._session.flush()
        return user

    async def set_role(self, user: User, role: UserRole) -> User:
        user.role = role
        await self._session.flush()
        return user
