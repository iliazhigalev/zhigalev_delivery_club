import aiohttp
from src.utils.logger import logger
import redis.asyncio as redis


class CurrencyService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_key = "usd_rub_rate"
        self.cache_ttl = 300

    async def get_usd_rate(self) -> float:
        cached_rate = await self.redis.get(self.cache_key)
        if cached_rate:
            logger.info("Using cached USD rate")
            return float(cached_rate)

        rate = await self._fetch_usd_rate()

        await self.redis.setex(self.cache_key, self.cache_ttl, str(rate))
        logger.info(f"Fetched new USD rate: {rate}")

        return rate

    async def _fetch_usd_rate(self) -> float:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"API returned status {response.status}")

                    data = await response.json()
                    usd_rate = data["Valute"]["USD"]["Value"]
                    logger.info(f"Fetched USD rate from API: {usd_rate}")
                    return usd_rate

        except Exception as e:
            logger.error(f"Error fetching USD rate: {e}")
            return 90.0
