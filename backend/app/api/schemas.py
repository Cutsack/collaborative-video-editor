"""
Pydantic schemas for API requests and responses
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: bool = False
    settings: Optional[Dict[str, Any]] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    owner: UserResponse
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


# Media schemas
class MediaFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    media_type: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class MediaFileCreate(MediaFileBase):
    project_id: int
    file_path: str


class MediaFileResponse(MediaFileBase):
    id: int
    project_id: int
    file_path: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Timeline schemas
class TimelineClipBase(BaseModel):
    clip_type: str
    start_time: float = Field(..., ge=0)
    duration: float = Field(..., gt=0)
    media_start: Optional[float] = Field(None, ge=0)
    media_end: Optional[float] = Field(None, ge=0)
    track_number: int = Field(..., ge=0)
    properties: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None


class TimelineClipCreate(TimelineClipBase):
    project_id: int
    media_file_id: Optional[int] = None


class TimelineClipUpdate(BaseModel):
    start_time: Optional[float] = Field(None, ge=0)
    duration: Optional[float] = Field(None, gt=0)
    media_start: Optional[float] = Field(None, ge=0)
    media_end: Optional[float] = Field(None, ge=0)
    track_number: Optional[int] = Field(None, ge=0)
    properties: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None


class TimelineClipResponse(TimelineClipBase):
    id: int
    project_id: int
    media_file_id: Optional[int] = None
    media_file: Optional[MediaFileResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Chat schemas
class ChatMessageBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    message_type: str = Field(default="text", regex="^(text|system|mention)$")


class ChatMessageCreate(ChatMessageBase):
    project_id: int


class ChatMessageResponse(ChatMessageBase):
    id: int
    project_id: int
    user_id: int
    user: UserResponse
    created_at: datetime
    
    class Config:
        from_attributes = True


# Upload schemas
class UploadRequest(BaseModel):
    filename: str
    content_type: str
    file_size: int
    project_id: int


class UploadResponse(BaseModel):
    upload_url: str
    file_key: str
    bucket: str


# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None


class CursorUpdateMessage(BaseModel):
    type: str = "cursor_update"
    x: float
    y: float
    timestamp: Optional[float] = None


class TimelineUpdateMessage(BaseModel):
    type: str = "timeline_update"
    action: str  # add, update, delete, move
    clip_data: Dict[str, Any]


class ChatMessageWebSocket(BaseModel):
    type: str = "chat_message"
    message: str
    timestamp: Optional[float] = None


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
