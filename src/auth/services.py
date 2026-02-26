from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from .models import User
from .schemas import UserCreateModel, UserLoginModel, UserResponseModel, Token
from .utils import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRY,
)
from sqlalchemy import select


class UserService:
    async def _get_user_by_email(
        self, email: str, session: AsyncSession
    ) -> User | None:
        """get user by email"""
        statement = await session.execute(select(User).where(User.email == email))
        user = statement.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist"
            )

    async def _check_user_exists(self, email: str, session: AsyncSession) -> bool:
        """checks if user already exists"""
        statement = await session.execute(select(User).where(User.email == email))
        existing_user = statement.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        return existing_user is None

    async def _create_new_user(
        self, user_data: UserCreateModel, session: AsyncSession
    ) -> User:
        """create new user record in db"""
        user = await self._check_user_exists(user_data.email, session)

        if user is None:
            new_user = User(
                email=user_data.email,
                fullname=user_data.full_name,
                phone_number=user_data.phone_number,
                password_hash=hash_password(user_data.password),
            )
        try:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
        except IntegrityError:
            await session.rollback()
        return new_user

    async def _verify_password(self, password: str, hashed_password: str):
        """verify user password"""
        is_valid_password = verify_password(password, hashed_password)
        if not is_valid_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or passwaord",
            )

    async def _generate_access_tokens(self, user: User) -> Token:
        """generate jwt access token"""

        access_token_expiry = timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        access_token = create_access_token(
            user_data={"sub": user.email, "user_id": str(user.id)},
            expiry=access_token_expiry,
        )
        return Token(access_token=access_token)
