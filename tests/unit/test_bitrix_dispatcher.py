from datetime import datetime, timezone

import pytest

from bot.config import BitrixSettings
from bot.core.enums import BitrixLeadSource, BitrixSyncStatus
from bot.core.exceptions import BitrixUnavailableError
from bot.db.models.bitrix_outbox import BitrixOutbox
from bot.services.bitrix_dispatcher import _send_one


class _FakeClient:
    def __init__(self, *, lead_id: int | None = None, exc: Exception | None = None) -> None:
        self._lead_id = lead_id
        self._exc = exc
        self.calls = 0
        self.last_fields: dict | None = None

    async def create_lead(self, fields: dict) -> int:
        self.calls += 1
        self.last_fields = fields
        if self._exc is not None:
            raise self._exc
        return self._lead_id


def _row() -> BitrixOutbox:
    return BitrixOutbox(
        source_type=BitrixLeadSource.CLIENT_REQUEST,
        source_id=1,
        payload={"lead_type": "request", "name": "Иван", "phone": "+700", "comment": None},
        status=BitrixSyncStatus.PENDING,
        attempts=0,
        next_attempt_at=datetime.now(tz=timezone.utc),
    )


def _settings(**overrides) -> BitrixSettings:
    base = {"enabled": True, "max_attempts": 3, "retry_backoff_base_seconds": 60}
    base.update(overrides)
    return BitrixSettings(**base)


@pytest.mark.asyncio
async def test_send_one_success_marks_sent():
    row = _row()
    now = datetime.now(tz=timezone.utc)
    ok = await _send_one(row, _FakeClient(lead_id=777), _settings(), now)

    assert ok is True
    assert row.status is BitrixSyncStatus.SENT
    assert row.bitrix_lead_id == 777
    assert row.last_error is None


@pytest.mark.asyncio
async def test_send_one_failure_schedules_retry():
    row = _row()
    now = datetime.now(tz=timezone.utc)
    ok = await _send_one(
        row, _FakeClient(exc=BitrixUnavailableError("boom")), _settings(max_attempts=3), now
    )

    assert ok is False
    assert row.status is BitrixSyncStatus.PENDING
    assert row.attempts == 1
    assert row.last_error == "boom"
    assert row.next_attempt_at > now  # сдвинут в будущее (backoff)


@pytest.mark.asyncio
async def test_send_one_marks_failed_after_max_attempts():
    row = _row()
    now = datetime.now(tz=timezone.utc)
    ok = await _send_one(
        row, _FakeClient(exc=BitrixUnavailableError("nope")), _settings(max_attempts=1), now
    )

    assert ok is False
    assert row.status is BitrixSyncStatus.FAILED
    assert row.attempts == 1


def test_responsible_ids_parses_csv():
    assert _settings(assigned_by_ids="25, 23 ,19,21").responsible_ids() == [25, 23, 19, 21]
    assert _settings().responsible_ids() == []
    assert _settings(assigned_by_ids="").responsible_ids() == []


@pytest.mark.asyncio
async def test_send_one_round_robin_assignee():
    settings = _settings(assigned_by_ids="25,23,19,21")
    now = datetime.now(tz=timezone.utc)

    # row.id=2 → 2 % 4 = 2 → ids[2] = 19
    row = _row()
    row.id = 2
    fake = _FakeClient(lead_id=1)
    await _send_one(row, fake, settings, now)
    assert fake.last_fields["ASSIGNED_BY_ID"] == 19

    # row.id=4 → 4 % 4 = 0 → ids[0] = 25 (круг замкнулся)
    row2 = _row()
    row2.id = 4
    fake2 = _FakeClient(lead_id=1)
    await _send_one(row2, fake2, settings, now)
    assert fake2.last_fields["ASSIGNED_BY_ID"] == 25


@pytest.mark.asyncio
async def test_send_one_omits_assignee_when_no_ids():
    row = _row()
    row.id = 7
    fake = _FakeClient(lead_id=1)
    await _send_one(row, fake, _settings(), datetime.now(tz=timezone.utc))
    assert "ASSIGNED_BY_ID" not in fake.last_fields
