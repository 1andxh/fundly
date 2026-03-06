from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.auth.routes import auth_router
from src.campaigns.routes import campaign_router
from .exception_handler import (
    fundly_exception_handler,
    request_validation_handler,
    general_exception_handler,
    RequestValidationError,
    FundlyException,
)

version = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("server is starting...")

    yield
    print("server is stopping")


app = FastAPI(
    version=version,
    title="Fundly-API",
    description="RESTful API for creating crowdfunding campaigns, processing donations, and managing fundraising data securely and at scale.",
    lifespan=lifespan,
)

# middleware


# exception_handlers
app.add_exception_handler(FundlyException, fundly_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(Exception, general_exception_handler)

# routers
app.include_router(auth_router, prefix=f"/api/auth", tags=["authentication"])
app.include_router(campaign_router, prefix=f"/api/campaigns", tags=["Campaigns"])
