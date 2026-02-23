from typing import Annotated, Any, override
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from .service import UserService
from .models import User
from .utils import decode_token

user_service = UserService()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
):
    """get current authenticated user"""
    token = credentials.credentials
    return user_service.get_current_user(token, session)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    "get current user and check if verified"
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified"
        )
    return current_user
