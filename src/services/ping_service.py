from fastapi import APIRouter

service_router = APIRouter()


@service_router.get("/ping")
async def ping():
    return {"Success": True}
