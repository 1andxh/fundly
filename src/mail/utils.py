import logging
from typing import Any

from fastapi import HTTPException, status
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)


def decode_url_safe_token(
    token: str, serializer: URLSafeTimedSerializer, max_age: int = 3600
) -> dict[str, Any]:
    try:
        token_data = serializer.loads(token, max_age=max_age)
        return token_data
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except BadSignature as e:
        logging.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not verify token"
        )
