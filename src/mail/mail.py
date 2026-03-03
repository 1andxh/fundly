from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from src.config import config
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
