import uuid
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


from api.routers import packages
from data.db import init_db
from tasks.scheduler import start_scheduler, run_once_now
from settings import settings


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("delivery_service")


app = FastAPI(
    title="Delivery Service",
    version="1.0",
    description="Микросервис для расчёта стоимости доставки и синхронизации пакетов.",
)

app.include_router(packages.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    cookie_name = settings.SESSION_COOKIE
    session_id = request.cookies.get(cookie_name)

    if not session_id:
        session_id = str(uuid.uuid4())
        new_cookie = True
    else:
        new_cookie = False

    request.state.session_id = session_id

    response = await call_next(request)
    if new_cookie:
        response.set_cookie(
            key=cookie_name,
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
        )
    return response


@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database connection...")
    await init_db()

    logger.info("Starting scheduler...")
    start_scheduler()

    logger.info("Application startup complete.")


@app.post("/admin/trigger_compute")
async def trigger_compute():
    """
    Админ-эндпоинт: принудительно запустить расчёт стоимости доставок.
    Используется для отладки и ручного тестирования.
    """
    count = await run_once_now()
    return {"processed_packages": count}


@app.get("/")
async def root():
    return {"message": "FastAPI backend is running"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST or "0.0.0.0",
        port=settings.PORT or 8000,
        reload=settings.DEBUG,
    )
