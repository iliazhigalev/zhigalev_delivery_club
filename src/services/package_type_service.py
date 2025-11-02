from src.schemas.package_type import PackageTypeList
from src.data.repositories.db_crud import UserDAL
from sqlalchemy.ext.asyncio import AsyncSession


async def _get_list_types_packages(session_db: AsyncSession) -> PackageTypeList:
    async with session_db.begin():
        user_dal = UserDAL(session_db)
        list_types_packages = await user_dal.get_all_types_packages()
        return list_types_packages
