from fastapi import Header, HTTPException


async def get_session_id(session_id: str = Header(..., alias="session-id")) -> str:
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID header is required")
    return session_id
