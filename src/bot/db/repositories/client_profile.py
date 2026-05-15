from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.client_profile import ClientProfile


class ClientProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> ClientProfile | None:
        stmt = select(ClientProfile).where(ClientProfile.user_id == user_id)
        return await self._session.scalar(stmt)

    async def upsert(
        self,
        *,
        user_id: int,
        phone: str | None = None,
        region: str | None = None,
        company: str | None = None,
        email: str | None = None,
    ) -> ClientProfile:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = ClientProfile(
                user_id=user_id, phone=phone, region=region, company=company, email=email
            )
            self._session.add(profile)
        else:
            if phone is not None:
                profile.phone = phone
            if region is not None:
                profile.region = region
            if company is not None:
                profile.company = company
            if email is not None:
                profile.email = email
        await self._session.flush()
        return profile
