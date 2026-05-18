from collections.abc import Sequence

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import RequestStatus
from bot.db.models.client_request import ClientRequest
from bot.db.models.dealer_profile import DealerProfile
from bot.db.models.product import Product
from bot.db.models.product_category import ProductCategory
from bot.db.models.user import User
from bot.db.repositories.client_request import ClientRequestRepository
from bot.db.repositories.user import UserRepository
from bot.schemas.marketing import (
    DashboardSnapshot,
    DealerBreakdownRow,
    ProductTopRow,
)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._requests = ClientRequestRepository(session)

    async def snapshot(self) -> DashboardSnapshot:
        users_by_role = await self._users.count_by_role()
        leads_by_status = await self._requests.count_grouped()
        return DashboardSnapshot(
            users_by_role=users_by_role,
            leads_by_status=leads_by_status,
        )

    async def dealers_breakdown(self, *, top_n: int = 10) -> Sequence[DealerBreakdownRow]:
        """Топ-N дилеров по числу назначенных лидов с разбивкой по статусам."""
        total_expr = func.count(ClientRequest.id)
        in_progress = func.sum(
            case((ClientRequest.status == RequestStatus.IN_PROGRESS, 1), else_=0)
        )
        done = func.sum(case((ClientRequest.status == RequestStatus.DONE, 1), else_=0))
        rejected = func.sum(
            case((ClientRequest.status == RequestStatus.REJECTED, 1), else_=0)
        )
        transferred = func.sum(
            case(
                (ClientRequest.status == RequestStatus.TRANSFERRED_TO_DEALER, 1),
                else_=0,
            )
        )
        stmt = (
            select(
                User.id.label("dealer_id"),
                User.full_name,
                DealerProfile.company,
                total_expr.label("total"),
                in_progress.label("in_progress"),
                done.label("done"),
                rejected.label("rejected"),
                transferred.label("transferred"),
            )
            .select_from(ClientRequest)
            .join(User, User.id == ClientRequest.assigned_dealer_id)
            .outerjoin(DealerProfile, DealerProfile.user_id == User.id)
            .group_by(User.id, User.full_name, DealerProfile.company)
            .order_by(desc("total"))
            .limit(top_n)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            DealerBreakdownRow(
                dealer_id=r.dealer_id,
                full_name=r.full_name,
                company=r.company,
                total=int(r.total or 0),
                in_progress=int(r.in_progress or 0),
                done=int(r.done or 0),
                rejected=int(r.rejected or 0),
                transferred=int(r.transferred or 0),
            )
            for r in rows
        ]

    async def top_products(self, *, top_n: int = 10) -> Sequence[ProductTopRow]:
        """Топ-N товаров по числу заявок (через client_requests.product_id)."""
        total_expr = func.count(ClientRequest.id).label("total")
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name,
                ProductCategory.name.label("category"),
                total_expr,
            )
            .select_from(ClientRequest)
            .join(Product, Product.id == ClientRequest.product_id)
            .join(ProductCategory, ProductCategory.id == Product.category_id)
            .group_by(Product.id, Product.name, ProductCategory.name)
            .order_by(desc("total"))
            .limit(top_n)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            ProductTopRow(
                product_id=r.product_id,
                name=r.name,
                category=r.category,
                requests_total=int(r.total or 0),
            )
            for r in rows
        ]
