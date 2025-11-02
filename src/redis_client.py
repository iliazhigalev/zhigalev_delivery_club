import redis.asyncio as redis
from src.settings import settings


async def get_redis_client():
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    try:
        await redis_client.ping()
    except Exception:
        raise

    return redis_client
