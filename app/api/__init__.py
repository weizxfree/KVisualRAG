from fastapi import APIRouter
from app.api.endpoints import sse
from app.api.endpoints import auth
from app.api.endpoints import chat
from app.api.endpoints import config
from app.api.endpoints import base
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_version_url)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(base.router, prefix="/base", tags=["base"])
api_router.include_router(sse.router, prefix="/sse", tags=["chat"])
api_router.include_router(config.router, prefix="/config", tags=["config"])