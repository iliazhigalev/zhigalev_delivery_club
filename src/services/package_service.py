from src.schemas.package_schemas import (
    PackageCreate,
    PackageListResponse,
    PackageResponse,
    PackageTypeBase,
)
from src.data.repositories.db_crud import UserDAL
from src.data.models.models import Package
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from fastapi import HTTPException
from src.schemas.schemas import PackageFilter, PaginationParams
from src.utils.logger import logger


async def _create_package(
    body: PackageCreate, session_id: str, session_db: AsyncSession
) -> Package:
    async with session_db.begin():
        user_dal = UserDAL(session_db)
        if body.type_id is not None:
            package_type = await user_dal.get_package_type_by_id(body.type_id)

            if not package_type:
                raise HTTPException(
                    status_code=404,
                    detail=f"The type of parcel with the ID {body.type_id} not found",
                )

        new_package = await user_dal.create_package(
            name=body.name,
            weight_kg=body.weight_kg,
            type_id=body.type_id,
            contents_value_usd=body.contents_value_usd,
            owner_session_id=session_id,
        )
        return new_package


async def _get_package_by_id(
    package_id: UUID, session_id: str, session_db: AsyncSession
) -> Package | None:
    user_dal = UserDAL(session_db)
    requested_package = await user_dal.get_package_by_id(package_id, session_id)
    return requested_package


async def _get_user_packages_with_filters(
    filters: PackageFilter,
    pagination: PaginationParams,
    session_id: str,
    session_db: AsyncSession,
) -> PackageListResponse:
    logger.info(f"Getting packages for session: {session_id}")

    actual_page = pagination.page if pagination.page is not None else 1
    actual_page_size = pagination.page_size if pagination.page_size is not None else 10

    if actual_page < 1:
        actual_page = 1
        logger.warning(f"Page corrected to {actual_page}")

    if actual_page_size < 1:
        actual_page_size = 10
        logger.warning(f"Page size corrected to {actual_page_size}")
    elif actual_page_size > 100:
        actual_page_size = 100
        logger.warning(f"Page size limited to {actual_page_size}")

    logger.info(
        f"Using pagination - page: {actual_page}, page_size: {actual_page_size}"
    )

    user_dal = UserDAL(session_db)

    skip = (actual_page - 1) * actual_page_size

    try:
        packages, total = await user_dal.get_user_packages_with_pagination(
            owner_session_id=session_id,
            type_id=filters.type_id,
            has_calculated_cost=filters.has_calculated_cost,
            skip=skip,
            limit=actual_page_size,
        )
    except Exception as e:
        logger.error(f"Error in database query: {e}")
        raise

    total_pages = 0
    if total > 0 and actual_page_size > 0:
        total_pages = (total + actual_page_size - 1) // actual_page_size
    else:
        total_pages = 1

    package_responses = []
    for package in packages:
        try:
            package_type_data = None
            if package.package_type:
                package_type_data = PackageTypeBase(
                    id=package.package_type.id,
                    name=package.package_type.name,
                    description=package.package_type.description,
                )

            package_response = PackageResponse(
                id=package.id,
                name=package.name,
                weight_kg=package.weight_kg,
                contents_value_usd=package.contents_value_usd,
                delivery_cost_rub=f"{package.delivery_cost_rub} RUB"
                if package.delivery_cost_rub
                else "Не рассчитано",
                package_type=package_type_data,
            )
            package_responses.append(package_response)
        except Exception as e:
            logger.error(
                f"Error creating PackageResponse for package {package.id}: {e}"
            )
            continue

    return PackageListResponse(
        packages=package_responses,
        total=total,
        page=actual_page,
        page_size=actual_page_size,
        total_pages=total_pages,
        has_next=actual_page < total_pages,
        has_prev=actual_page > 1,
    )
