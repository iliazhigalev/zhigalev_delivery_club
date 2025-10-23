from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy import select

from src.schemas import PackageCreate, PackageOut
from src.services.package_service import (
    create_package,
    list_package_types,
    list_own_packages,
    get_package_by_id,
    bind_package_to_company,
)
from src.data.models import PackageType
from src.data.db import AsyncSessionLocal


router = APIRouter(prefix="/packages", tags=["Packages"])


def get_session_id(request: Request) -> str:
    """
    Извлекает session_id, установленный middleware (в main.py).
    """
    return request.state.session_id


@router.post("/", response_model=PackageOut, status_code=status.HTTP_201_CREATED)
async def register_package(payload: PackageCreate, request: Request):
    """
    Создаёт новую посылку для текущего пользователя.
    """
    owner_session = request.state.session_id
    pkg = await create_package(payload, owner_session)

    # Получаем название типа
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(PackageType).where(PackageType.id == pkg.type_id)
        )
        res.scalar_one()

    out = PackageOut.from_orm(pkg)
    return out


@router.get("/types", response_model=List[dict])
async def get_types():
    """
    Возвращает список всех доступных типов посылок.
    """
    types = await list_package_types()
    return [{"id": t.id, "name": t.name} for t in types]


@router.get("/", response_model=List[PackageOut])
async def get_my_packages(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(
        10, ge=1, le=100, description="Количество элементов на странице"
    ),
    type_id: Optional[int] = Query(None, description="Фильтр по типу посылки"),
    has_delivery: Optional[bool] = Query(
        None, description="Фильтр по наличию стоимости доставки"
    ),
):
    """
    Возвращает список собственных посылок с фильтрацией и пагинацией.
    """
    owner = request.state.session_id
    pkgs = await list_own_packages(owner, page, per_page, type_id, has_delivery)
    out = []

    async with AsyncSessionLocal() as session:
        for p in pkgs:
            res = await session.execute(
                select(PackageType).where(PackageType.id == p.type_id)
            )
            res.scalar_one()
            po = PackageOut.from_orm(p)
            out.append(po)

    return out


@router.get("/{pkg_id}", response_model=PackageOut)
async def get_package(pkg_id: UUID, request: Request):
    """
    Возвращает детальную информацию о посылке по её ID.
    Только если она принадлежит текущему пользователю.
    """
    owner = request.state.session_id
    p = await get_package_by_id(owner, pkg_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Package not found"
        )

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(PackageType).where(PackageType.id == p.type_id)
        )
        res.scalar_one()

    out = PackageOut.from_orm(p)
    return out


@router.post("/{pkg_id}/bind-company")
async def bind_company(
    pkg_id: UUID, company_id: int = Query(..., gt=0), request: Request = None
):
    """
    Привязывает посылку к компании (если она ещё не занята).
    Возвращает статус или ошибку 409, если уже привязана.
    """
    success = await bind_package_to_company(pkg_id, company_id)

    if success:
        return {"status": "bound", "company_id": company_id}

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Already claimed by another company",
    )
