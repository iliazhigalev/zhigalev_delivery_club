from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, APIRouter
from src.schemas.package_schemas import (
    PackageCreate,
    PackageCreateResponse,
    PackageResponse,
    PackageListResponse,
)
from src.data.db.session import get_db
from src.dependencies.dependencies import get_session_id
from src.services.package_service import (
    _create_package,
    _get_package_by_id,
    _get_user_packages_with_filters,
)
from src.services.package_type_service import _get_list_types_packages
from src.schemas.package_type import PackageTypeList, PackageTypeResponse
from src.schemas.schemas import PackageFilter, PaginationParams
from src.utils.logger import logger

router = APIRouter()


@router.post("/packages", response_model=PackageCreateResponse)
async def create_package_for_user(
    package_data: PackageCreate,
    session_id: str = Depends(get_session_id),
    session_db: AsyncSession = Depends(get_db),
) -> PackageCreateResponse:
    try:
        return await _create_package(package_data, session_id, session_db)
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error:{err}")


@router.get("/package-types", response_model=PackageTypeList)
async def get_all_types(db: AsyncSession = Depends(get_db)) -> PackageTypeList:
    list_types = await _get_list_types_packages(db)
    if not list_types:
        return PackageTypeList(package_types=[])
    package_types = [PackageTypeResponse(id=item.id) for item in list_types]

    return PackageTypeList(package_types=package_types)


@router.get("/packages", response_model=PackageListResponse)
async def get_my_packages(
    type_id_for_filter: UUID | None = None,
    has_calculated_cost: bool | None = None,
    page: int | None = None,
    page_size: int | None = None,
    session_id: str = Depends(get_session_id),
    session_db: AsyncSession = Depends(get_db),
) -> PackageListResponse:
    try:
        filters = PackageFilter(
            type_id=type_id_for_filter, has_calculated_cost=has_calculated_cost
        )

        pagination = PaginationParams(page=page, page_size=page_size)
        logger.info(
            f"Pagination params - page: {pagination.page}, page_size: {pagination.page_size}"
        )

        list_package_user = await _get_user_packages_with_filters(
            filters, pagination, session_id, session_db
        )
    except Exception as err:
        logger.error(f"Error getting user packages: {err}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return list_package_user


@router.get("/{package_id}", response_model=PackageResponse)
async def get_info_package_by_id(
    package_id: UUID,
    session_id: str = Depends(get_session_id),
    session_db: AsyncSession = Depends(get_db),
):
    requested_package = await _get_package_by_id(package_id, session_id, session_db)

    if not requested_package:
        raise HTTPException(status_code=404, detail="Package not found")
    requested_package.delivery_cost_rub = (
        f"{requested_package.delivery_cost_rub} RUB"
        if requested_package.delivery_cost_rub
        else "Не рассчитано"
    )
    return requested_package
