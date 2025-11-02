from src.data.db.session import get_db
from src.utils.logger import logger
from src.data.models.models import Package
from sqlalchemy import select
from src.redis_client import get_redis_client
from src.utils.currency_utils import CurrencyService
from src.utils.delivery_calculator import DeliveryCalculator
import asyncio


def calculating_cost_unprocessed_parcels():
    return asyncio.run(_async_calculating_cost_unprocessed_parcels())


async def _async_calculating_cost_unprocessed_parcels():
    async for session_db in get_db():
        try:
            query = select(Package).where(Package.delivery_cost_rub.is_(None))
            result = await session_db.execute(query)
            packages = result.scalars().all()

            if not packages:
                logger.info("No packages without delivery cost found")
                return {"processed": 0, "message": "No packages to process"}

            redis_client = await get_redis_client()
            currency_service = CurrencyService(redis_client)
            calculator = DeliveryCalculator(currency_service)

            processed_count = 0
            errors = []

            for package in packages:
                try:
                    delivery_cost = await calculator.calculate_delivery_cost(
                        package.weight_kg, package.contents_value_usd
                    )

                    package.delivery_cost_rub = delivery_cost
                    processed_count += 1

                    logger.info(
                        f"Calculated delivery cost for package {package.id}: {delivery_cost} RUB"
                    )

                except Exception as e:
                    error_msg = f"Error calculating cost for package {package.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            await session_db.commit()
            await redis_client.close()

            result = {
                "processed": processed_count,
                "total_found": len(packages),
                "errors": errors,
            }

            logger.info(
                f"Successfully processed {processed_count} out of {len(packages)} packages"
            )
            return result

        except Exception as e:
            logger.error(f"Error in calculating_cost_unprocessed_parcels: {e}")
            return {"processed": 0, "error": str(e)}
