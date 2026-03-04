from pathlib import Path
from typing import Sequence
from pydantic import NameEmail
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.config import config


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = Path(BASE_DIR, "templates")

mail_config = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    USE_CREDENTIALS=config.USE_CREDENTIALS,
    VALIDATE_CERTS=config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=(
        TEMPLATE_FOLDER if TEMPLATE_FOLDER.is_dir() else None
    ),  # only for when mail is up but no templates folder so the app doesn't crash
)

mail = FastMail(config=mail_config)


def create_message(recipients, subject: str, body: str) -> MessageSchema:
    message = MessageSchema(
        recipients=recipients,
        subject=subject,
        body=body,
        subtype=MessageType.html,
    )
    return message
