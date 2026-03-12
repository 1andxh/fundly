import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

# import bcrypt
import jwt
from src.config import config


jwt_secret_key = config.JWT_SECRET
jwt_algorithm = config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRY = 3600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# bcrypt
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    user_data: dict,
    expiry: timedelta = timedelta(seconds=ACCESS_TOKEN_EXPIRY),
    refresh: bool = False,
):
    now = datetime.now(timezone.utc)

    payload = {
        "user": user_data,
        "exp": now + expiry,
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
        "iat": now,
    }

    token = jwt.encode(payload=payload, key=jwt_secret_key, algorithm=jwt_algorithm)
    return token


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            jwt=token,
            key=jwt_secret_key,
            algorithms=[jwt_algorithm],
        )
        return payload
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None
