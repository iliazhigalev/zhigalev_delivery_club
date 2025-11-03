from decimal import Decimal
from src.utils.logger import logger
from src.utils.currency_utils import CurrencyService


class DeliveryCalculator:
    def __init__(self, currency_service: CurrencyService):
        self.currency_service = currency_service

    async def calculate_delivery_cost(
        self, weight_kg: Decimal, contents_value_usd: Decimal
    ) -> Decimal:
        usd_rate = await self.currency_service.get_usd_rate()

        cost = (
            weight_kg * Decimal("0.5") + contents_value_usd * Decimal("0.01")
        ) * Decimal(str(usd_rate))
        cost = cost.quantize(Decimal("0.01"))

        logger.debug(
            f"Calculated delivery cost: {cost} (weight: {weight_kg}, value: {contents_value_usd}, rate: {usd_rate})"
        )
        return cost
