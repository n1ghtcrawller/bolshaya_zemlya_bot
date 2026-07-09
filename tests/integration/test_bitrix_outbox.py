from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from bot.config import BitrixSettings
from bot.core.enums import BitrixLeadSource, BitrixSyncStatus, LeadType, UserRole
from bot.core.exceptions import BitrixUnavailableError
from bot.db.models.bitrix_outbox import BitrixOutbox
from bot.db.repositories.bitrix_outbox import BitrixOutboxRepository
from bot.schemas.request import ClientRequestCreate
from bot.services.bitrix_dispatcher import dispatch_pending_leads
from bot.services.request_service import RequestService


def _payload() -> ClientRequestCreate:
    return ClientRequestCreate(
        contact_name="Иван",
        contact_phone="+71234567890",
        comment="нужна техника",
        lead_type=LeadType.REQUEST,
    )


@pytest.mark.asyncio
async def test_create_for_user_enqueues_outbox_when_enabled(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    await session.flush()

    service = RequestService(session, BitrixSettings(enabled=True))
    request = await service.create_for_user(client.id, _payload())

    rows = (await session.scalars(select(BitrixOutbox))).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.source_type is BitrixLeadSource.CLIENT_REQUEST
    assert row.source_id == request.id
    assert row.status is BitrixSyncStatus.PENDING
    assert row.payload["lead_type"] == "request"
    assert row.payload["phone"] == "+71234567890"
    assert row.payload["telegram_id"] == client.telegram_id


@pytest.mark.asyncio
async def test_create_for_user_skips_outbox_when_disabled(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    await session.flush()

    # bitrix_settings=None → enqueue не выполняется
    await RequestService(session).create_for_user(client.id, _payload())

    rows = (await session.scalars(select(BitrixOutbox))).all()
    assert rows == []


class _FakeClient:
    def __init__(self, *, lead_id=None, exc=None) -> None:
        self._lead_id = lead_id
        self._exc = exc

    async def create_lead(self, fields: dict) -> int:
        if self._exc is not None:
            raise self._exc
        return self._lead_id


@pytest.mark.asyncio
async def test_dispatch_pending_leads_marks_sent(sessionmaker, make_user):
    async with sessionmaker() as s:
        client = make_user(s, role=UserRole.CLIENT)
        await s.flush()
        await BitrixOutboxRepository(s).create(
            source_type=BitrixLeadSource.CLIENT_REQUEST,
            source_id=client.id,
            payload={"lead_type": "request", "name": "Иван", "phone": "+700", "comment": None},
        )
        await s.commit()

    sent = await dispatch_pending_leads(
        sessionmaker, _FakeClient(lead_id=555), BitrixSettings(enabled=True)
    )
    assert sent == 1

    async with sessionmaker() as s:
        row = (await s.scalars(select(BitrixOutbox))).one()
        assert row.status is BitrixSyncStatus.SENT
        assert row.bitrix_lead_id == 555


@pytest.mark.asyncio
async def test_dispatch_pending_leads_retries_on_error(sessionmaker, make_user):
    async with sessionmaker() as s:
        client = make_user(s, role=UserRole.CLIENT)
        await s.flush()
        await BitrixOutboxRepository(s).create(
            source_type=BitrixLeadSource.CLIENT_REQUEST,
            source_id=client.id,
            payload={"lead_type": "request", "name": "Иван", "phone": "+700", "comment": None},
        )
        await s.commit()

    sent = await dispatch_pending_leads(
        sessionmaker,
        _FakeClient(exc=BitrixUnavailableError("down")),
        BitrixSettings(enabled=True, max_attempts=5),
    )
    assert sent == 0

    now = datetime.now(tz=timezone.utc)
    async with sessionmaker() as s:
        row = (await s.scalars(select(BitrixOutbox))).one()
        assert row.status is BitrixSyncStatus.PENDING
        assert row.attempts == 1
        assert row.last_error == "down"
        # next_attempt_at сдвинут в будущее → строка больше не «созревшая»
        assert not (await BitrixOutboxRepository(s).list_due(now))
