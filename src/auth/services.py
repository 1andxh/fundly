from datetime import timedelta

from fastapi import HTTPException, status, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .schemas import Token, UserCreateModel, UserResponseModel
from .utils import (
    ACCESS_TOKEN_EXPIRY,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.mail.utils import decode_url_safe_token
from src.mail.services import MailService
from fastapi.responses import JSONResponse

REFRESH_TOKEN_EXPIRY_DAYS = 7
mail_service = MailService()


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserService:
    async def _update_user_is_verified(
        self, user: User, update_dict: dict, session: AsyncSession
    ):
        for k, v in update_dict.items():
            setattr(user, k, v)
        await session.flush()
        return user

    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        normalized_email = normalize_email(email)
        result = await session.execute(
            select(User).where(func.lower(User.email) == normalized_email)
        )
        return result.scalar_one_or_none()

    async def check_user_exists(self, email: str, session: AsyncSession) -> bool:
        user = await self.get_user_by_email(email, session)
        return user is not None

    async def create_user(
        self, user_data: UserCreateModel, session: AsyncSession
    ) -> User:
        normalized_email = normalize_email(user_data.email)

        if await self.check_user_exists(normalized_email, session):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        new_user = User(
            email=normalized_email,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            password_hash=hash_password(user_data.password),
        )

        session.add(new_user)
        try:
            await session.flush()
            await session.refresh(new_user)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        return new_user

    async def authenticate_user(
        self, email: str, password: str, session: AsyncSession
    ) -> User:
        user = await self.get_user_by_email(email, session)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        return user

    def generate_token_pair(self, user: User) -> Token:
        access_token_expiry = timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        access_token = create_access_token(
            user_data={"email": user.email, "user_id": str(user.id)},
            expiry=access_token_expiry,
            refresh=False,
        )
        refresh_token = create_access_token(
            user_data={"email": user.email, "user_id": str(user.id)},
            expiry=timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
            refresh=True,
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    def refresh_tokens(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        if not payload.get("refresh", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required",
            )

        user_data = payload.get("user") or {}
        email = user_data.get("email")
        user_id = user_data.get("user_id")
        if not email or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        access_token = create_access_token(
            user_data={"email": email, "user_id": user_id},
            refresh=False,
        )
        new_refresh_token = create_access_token(
            user_data={"email": email, "user_id": user_id},
            expiry=timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
            refresh=True,
        )
        return Token(access_token=access_token, refresh_token=new_refresh_token)

    async def get_current_user(self, token: str, session: AsyncSession) -> User:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        if payload.get("refresh", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token required",
            )

        user_data = payload.get("user") or {}
        email = user_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user = await self.get_user_by_email(email, session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    async def verify_user(self, token: str, session: AsyncSession):
        token_data = decode_url_safe_token(token, mail_service.email_serializer)
        email = token_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid verification token",
            )
        user = await self.get_user_by_email(email, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )
        if user.is_verified:
            return JSONResponse(
                content={"message": "Account already verified"},
                status_code=status.HTTP_200_OK,
            )
        await self._update_user_is_verified(user, {"is_verified": True}, session)
        return JSONResponse(content={"message": "Account succesfully verified"})
