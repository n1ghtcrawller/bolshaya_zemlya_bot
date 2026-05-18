from datetime import datetime, timezone

import pytest

from bot.core.enums import ContentStatus, ContentType
from bot.services.content_service import ContentService


@pytest.mark.asyncio
async def test_create_without_date_is_draft(session, make_user):
    author = make_user(session)
    await session.flush()
    item = await ContentService(session).create(
        content_type=ContentType.IDEA,
        title="Идея",
        body=None,
        region=None,
        scheduled_at=None,
        author_user_id=author.id,
    )
    assert item.status is ContentStatus.DRAFT


@pytest.mark.asyncio
async def test_create_with_date_is_scheduled(session, make_user):
    author = make_user(session)
    await session.flush()
    when = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
    item = await ContentService(session).create(
        content_type=ContentType.PLAN,
        title="Пост",
        body=None,
        region=None,
        scheduled_at=when,
        author_user_id=author.id,
    )
    assert item.status is ContentStatus.SCHEDULED
    assert item.scheduled_at == when


@pytest.mark.asyncio
async def test_submit_for_approval_overrides_date(session, make_user):
    author = make_user(session)
    await session.flush()
    when = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
    item = await ContentService(session).create(
        content_type=ContentType.PLAN,
        title="Пост",
        body=None,
        region=None,
        scheduled_at=when,
        author_user_id=author.id,
        submit_for_approval=True,
    )
    # submit_for_approval имеет приоритет над scheduled_at
    assert item.status is ContentStatus.PENDING_APPROVAL


@pytest.mark.asyncio
async def test_scheduled_content_type_without_date_is_draft(session, make_user):
    """Тип SCHEDULED без даты — это всё равно черновик (тип и статус — разные оси)."""
    author = make_user(session)
    await session.flush()
    item = await ContentService(session).create(
        content_type=ContentType.SCHEDULED,
        title="Отложка без даты",
        body=None,
        region=None,
        scheduled_at=None,
        author_user_id=author.id,
    )
    assert item.status is ContentStatus.DRAFT
    assert item.type is ContentType.SCHEDULED
