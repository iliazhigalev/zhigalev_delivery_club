import logging
from decimal import Decimal
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from uuid import UUID
from src.data.models.models import Package, PackageType

logger = logging.getLogger(__name__)


class UserDAL:
    """Data access level for interaction with the application"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_package(
        self,
        name: str,
        weight_kg: Decimal,
        type_id: UUID,
        contents_value_usd: Decimal,
        owner_session_id: str,
    ) -> Package:
        new_package = Package(
            name=name,
            weight_kg=weight_kg,
            type_id=type_id,
            contents_value_usd=contents_value_usd,
            owner_session_id=owner_session_id,
        )
        self.db_session.add(new_package)
        await self.db_session.flush()
        return new_package

    async def get_all_types_packages(self) -> list[PackageType]:
        query = select(PackageType).order_by(PackageType.id)
        result = await self.db_session.execute(query)
        if result is None:
            return []
        return result.scalars().all()

    async def get_package_by_id(
        self, package_id: UUID, owner_session_id: str
    ) -> Package | None:
        query = (
            select(Package)
            .where(
                and_(
                    Package.id == package_id,
                    Package.owner_session_id == owner_session_id,
                )
            )
            .options(selectinload(Package.package_type))
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_package_type_by_id(self, type_id: UUID) -> PackageType | None:
        query = select(PackageType).where(PackageType.id == type_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_packages_with_pagination(
        self,
        owner_session_id: str,
        type_id: UUID | None = None,
        has_calculated_cost: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> (list[Package], int):
        query = (
            select(Package)
            .where(Package.owner_session_id == owner_session_id)
            .options(selectinload(Package.package_type))
        )

        count_query = (
            select(func.count())
            .select_from(Package)
            .where(Package.owner_session_id == owner_session_id)
        )

        if type_id is not None:
            query = query.where(Package.type_id == type_id)
            count_query = count_query.where(Package.type_id == type_id)

        if has_calculated_cost is not None:
            if has_calculated_cost:
                query = query.where(Package.delivery_cost_rub.is_not(None))
                count_query = count_query.where(Package.delivery_cost_rub.is_not(None))
            else:
                query = query.where(Package.delivery_cost_rub.is_(None))
                count_query = count_query.where(Package.delivery_cost_rub.is_(None))

        query = query.order_by(Package.weight_kg.desc()).offset(skip).limit(limit)

        # Выполняем запросы
        result = await self.db_session.execute(query)
        packages = result.scalars().all()

        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        return packages, total
