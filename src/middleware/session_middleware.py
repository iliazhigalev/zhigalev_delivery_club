import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

SESSION_COOKIE_NAME = "session_id"
SESSION_TTL_SECONDS = 30 * 24 * 3600


class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        redis = request.app.state.redis

        session_id = request.cookies.get(SESSION_COOKIE_NAME)

        if not session_id:
            session_id = str(uuid.uuid4())

            await redis.setex(f"session:{session_id}", SESSION_TTL_SECONDS, "active")

            request.state.session_id = session_id
            response = await call_next(request)

            response.set_cookie(
                SESSION_COOKIE_NAME,
                session_id,
                httponly=True,
                max_age=SESSION_TTL_SECONDS,
                samesite="lax",
            )
            return response

        request.state.session_id = session_id
        await redis.expire(f"session:{session_id}", SESSION_TTL_SECONDS)

        response = await call_next(request)
        return response
