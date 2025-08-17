from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from . import crud, models
from .database import AsyncSessionLocal

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> models.User:
    session_id = request.cookies.get("session_id")
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    user = await crud.get_user_by_session_id(db, session_id=session_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    return user