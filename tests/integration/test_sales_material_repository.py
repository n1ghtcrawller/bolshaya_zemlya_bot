import pytest

from bot.core.enums import (
    ApprovalStatus,
    SalesMaterialCategory,
    SalesMaterialFileType,
    UserRole,
)
from bot.db.repositories.sales_material import SalesMaterialRepository


@pytest.mark.asyncio
async def test_list_by_category_filters_by_approval(session, make_user):
    marketer = make_user(session, role=UserRole.MARKETING)
    dealer = make_user(session, role=UserRole.DEALER)
    await session.flush()
    repo = SalesMaterialRepository(session)

    approved = await repo.create(
        category=SalesMaterialCategory.CATALOGS,
        title="Утверждённый",
        description=None,
        file_type=SalesMaterialFileType.DOCUMENT,
        telegram_file_id="approved-id",
        uploaded_by_user_id=marketer.id,
        approval_status=ApprovalStatus.APPROVED,
    )
    await repo.create(
        category=SalesMaterialCategory.CATALOGS,
        title="На согласовании",
        description=None,
        file_type=SalesMaterialFileType.DOCUMENT,
        telegram_file_id="pending-id",
        uploaded_by_user_id=dealer.id,
        approval_status=ApprovalStatus.PENDING,
    )

    # По умолчанию — только approved
    visible = await repo.list_by_category(SalesMaterialCategory.CATALOGS)
    assert [m.id for m in visible] == [approved.id]

    # Если фильтр отключить — оба
    all_in_cat = await repo.list_by_category(
        SalesMaterialCategory.CATALOGS, approval_status=None
    )
    assert len(all_in_cat) == 2


@pytest.mark.asyncio
async def test_list_pending_returns_only_pending(session, make_user):
    marketer = make_user(session, role=UserRole.MARKETING)
    dealer = make_user(session, role=UserRole.DEALER)
    await session.flush()
    repo = SalesMaterialRepository(session)

    await repo.create(
        category=SalesMaterialCategory.PRESENTATIONS,
        title="A",
        description=None,
        file_type=SalesMaterialFileType.PHOTO,
        telegram_file_id="a",
        uploaded_by_user_id=marketer.id,
        approval_status=ApprovalStatus.APPROVED,
    )
    pending = await repo.create(
        category=SalesMaterialCategory.PRESENTATIONS,
        title="B",
        description=None,
        file_type=SalesMaterialFileType.PHOTO,
        telegram_file_id="b",
        uploaded_by_user_id=dealer.id,
        approval_status=ApprovalStatus.PENDING,
    )

    result = await repo.list_pending()
    assert [m.id for m in result] == [pending.id]
