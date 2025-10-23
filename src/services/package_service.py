import logging
from decimal import Decimal
from typing import List, Optional

import httpx
import redis.asyncio as redis
from sqlalchemy import select, update as sa_update

from src.data.db import AsyncSessionLocal
from src.data.models import Package, PackageType
from src.settings import settings

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_DSN, decode_responses=True)


async def create_package(data, owner_session_id: str) -> Package:
    """
    Создаёт новую посылку в БД.
    """
    async with AsyncSessionLocal() as session:
        pkg = Package(
            name=data.name,
            weight_kg=data.weight_kg,
            type_id=data.type_id,
            contents_value_usd=data.contents_value_usd,
            owner_session_id=owner_session_id,
        )
        session.add(pkg)
        await session.commit()
        await session.refresh(pkg)
        return pkg


async def list_package_types() -> List[PackageType]:
    """
    Возвращает список всех типов посылок.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PackageType))
        return result.scalars().all()


async def list_own_packages(
    owner_session_id: str,
    page: int = 1,
    per_page: int = 10,
    type_id: Optional[int] = None,
    has_delivery: Optional[bool] = None,
) -> List[Package]:
    """
    Возвращает список посылок текущего пользователя с фильтрацией и пагинацией.
    """
    async with AsyncSessionLocal() as session:
        q = select(Package).where(Package.owner_session_id == owner_session_id)

        if type_id is not None:
            q = q.where(Package.type_id == type_id)
        if has_delivery is True:
            q = q.where(Package.delivery_cost_rub.isnot(None))
        elif has_delivery is False:
            q = q.where(Package.delivery_cost_rub.is_(None))

        q = (
            q.order_by(Package.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        res = await session.execute(q)
        return res.scalars().all()


async def get_package_by_id(owner_session_id: str, pkg_id: int) -> Optional[Package]:
    """
    Возвращает посылку по ID, если она принадлежит указанной сессии.
    """
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(Package).where(
                Package.id == pkg_id, Package.owner_session_id == owner_session_id
            )
        )
        return res.scalar_one_or_none()


async def get_usd_to_rub_rate() -> Decimal:
    """
    Возвращает курс USD→RUB из Redis или, если нет — запрашивает с сайта ЦБ РФ.
    """
    cached = await redis_client.get(settings.CBR_CACHE_KEY)
    if cached:
        try:
            return Decimal(cached)
        except Exception:
            logger.warning("Некорректные данные курса в Redis, запрашиваю заново...")

    async with httpx.AsyncClient() as client:
        r = await client.get(settings.CBR_URL, timeout=10)
        r.raise_for_status()
        data = r.json()

    usd = data.get("Valute", {}).get("USD", {}).get("Value")
    if usd is None:
        raise RuntimeError("CBR response missing USD value")

    rate = Decimal(str(usd))
    await redis_client.set(
        settings.CBR_CACHE_KEY, str(rate), ex=settings.CBR_TTL_SECONDS
    )
    logger.info(f"Fetched USD→RUB rate from CBR: {rate}")
    return rate


async def compute_delivery_costs_for_unprocessed() -> int:
    """
    Рассчитывает стоимость доставки для всех посылок,
    у которых delivery_cost_rub ещё не задан.
    """
    rate = await get_usd_to_rub_rate()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Package).where(Package.delivery_cost_rub.is_(None))
        )
        packages = result.scalars().all()

        for pkg in packages:
            weight = Decimal(str(pkg.weight_kg))
            contents = Decimal(str(pkg.contents_value_usd))
            cost = (weight * Decimal("0.5") + contents * Decimal("0.01")) * rate
            cost = cost.quantize(Decimal("0.01"))  # округление до 2 знаков

            await session.execute(
                sa_update(Package)
                .where(Package.id == pkg.id)
                .values(delivery_cost_rub=cost)
            )

        await session.commit()

    logger.info(
        f"Computed delivery costs for {len(packages)} packages using rate {rate}"
    )
    return len(packages)


async def bind_package_to_company(
    pkg_id: int, company_id: int, owner_session_id: Optional[str] = None
) -> bool:
    """
    Привязывает посылку к компании, если она ещё никому не принадлежит (атомарно).
    Возвращает True, если операция успешна, False — если уже занята.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            sa_update(Package)
            .where(Package.id == pkg_id, Package.company_id.is_(None))
            .values(company_id=company_id)
            .returning(Package.id, Package.company_id)
        )
        res = await session.execute(stmt)
        await session.commit()
        row = res.first()
        return bool(row)
