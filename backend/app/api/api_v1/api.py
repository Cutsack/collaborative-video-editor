"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, projects, media, timeline, chat

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
