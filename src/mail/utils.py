import logging
from typing import Any

from fastapi import HTTPException, status, BackgroundTasks
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)

from .mail import create_message, mail
from src.templates import templates
from urllib.parse import quote
from .services import MailService
from src.auth.models import User
from datetime import datetime, timezone

mail_service = MailService()


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


# MAIL SENDER
async def send_verification_mail(new_user: User, bg_task: BackgroundTasks):
    # token gen
    token = mail_service.create_email_verification_token(data={"email": new_user.email})
    safe_token = quote(token, safe="")
    verification_link = f"https://127.0.0.1:8000/api/auth/verify?token={safe_token}"

    # render html
    template = templates.templates.get_template("verify_email.html")

    html_content = template.render(
        {
            "user_name": new_user.full_name,
            "link": verification_link,
            "year": datetime.now(timezone.utc),
        }
    )

    message = create_message(
        recipients=[new_user.email],
        subject="Verify you Fundly account",
        body=html_content,
    )

    bg_task.add_task(mail.send_message, message)
