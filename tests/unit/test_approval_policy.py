import pytest

from bot.core.enums import UserRole
from bot.services.approval_policy import can_approve_marketing


@pytest.mark.asyncio
async def test_head_of_marketing_always_can_approve(session, make_user):
    head = make_user(session, role=UserRole.HEAD_OF_MARKETING)
    await session.flush()
    assert await can_approve_marketing(session, head) is True


@pytest.mark.asyncio
async def test_non_marketing_role_cannot_approve(session, make_user):
    sales = make_user(session, role=UserRole.SALES)
    await session.flush()
    assert await can_approve_marketing(session, sales) is False


@pytest.mark.asyncio
async def test_marketer_can_approve_only_if_no_head(session, make_user):
    # Нет head_of_marketing → fallback к маркетологу
    marketer = make_user(session, role=UserRole.MARKETING)
    await session.flush()
    assert await can_approve_marketing(session, marketer) is True

    # Назначили head_of_marketing → обычный маркетолог больше не может
    make_user(session, role=UserRole.HEAD_OF_MARKETING)
    await session.flush()
    assert await can_approve_marketing(session, marketer) is False
