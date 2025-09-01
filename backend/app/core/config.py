"""
Configuration settings for the application
"""

from typing import List
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Collaborative Video Editor"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/video_editor"
    
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MinIO/S3
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_SECURE: bool = False
    
    # AWS S3 (for production)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Media
    MAX_FILE_SIZE: str = "100MB"
    ALLOWED_VIDEO_FORMATS: List[str] = ["mp4", "avi", "mov", "wmv", "flv", "webm"]
    ALLOWED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "aac", "ogg", "flac"]
    ALLOWED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "gif", "bmp"]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
