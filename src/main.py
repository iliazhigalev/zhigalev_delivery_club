import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.routing import APIRouter
from src.settings import settings
from src.services.ping_service import service_router
from src.api.handlers import router
from src.redis_client import get_redis_client
from middleware.session_middleware import SessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = await get_redis_client()
    app.state.redis = redis_client

    yield

    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Delivery Service",
    description="Микросервис для расчёта стоимости доставки и синхронизации пакетов.",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware)

main_api_router = APIRouter()
main_api_router.include_router(
    router, prefix="/api", tags=["package_and_package_types"]
)
main_api_router.include_router(service_router, tags=["service"])
app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
