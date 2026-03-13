from fastapi import APIRouter, Depends, status, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from .dependencies import get_current_active_user
from .models import User
from .schemas import Token, UserCreateModel, UserLoginModel, UserResponseModel
from .services import UserService
from src.mail.schemas import EmailValidator
from src.mail.utils import decode_url_safe_token
from src.mail.mail import create_message, mail
from datetime import datetime as dt
from src.templates.templates import templates
from src.mail.services import MailService
from src.mail.utils import send_verification_mail

auth_router = APIRouter()
user_service = UserService()
refresh_security = HTTPBearer()


@auth_router.get("/health")
async def auth_health():
    return {"status": "ok", "service": "auth"}


@auth_router.post("/send-mail")
async def send_mail(emails: EmailValidator, bg_task: BackgroundTasks):
    recipients = emails.address
    template = templates.get_template("base.html")

    html_content = template.render({"year": dt.now().year})

    message = create_message(
        recipients=recipients,
        subject="Fundly.Crowdfund.Convenience",
        body=html_content,
    )
    bg_task.add_task(mail.send_message, message)
    return {"message": "Email sent successfully"}


@auth_router.post(
    "/signup",
    response_model=UserResponseModel,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    bg_task: BackgroundTasks,
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session),
):
    new_user = await user_service.create_user(user_data, session)
    await send_verification_mail(new_user, bg_task)
    return JSONResponse(
        content={
            "message": "A link to verify your account has been sent to your email"
        },
        status_code=200,
    )


@auth_router.get("/verify")
async def verify_user(token: str, session: AsyncSession = Depends(get_session)):

    return await user_service.verify_user(token, session)


@auth_router.post("/login", response_model=Token)
async def login(
    credentials: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    user = await user_service.authenticate_user(
        credentials.email,
        credentials.password,
        session,
    )
    return user_service.generate_token_pair(user)


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_security),
):
    return user_service.refresh_tokens(credentials.credentials)


@auth_router.get("/me", response_model=UserResponseModel)
async def me(current_user: User = Depends(get_current_active_user)):
    return current_user
