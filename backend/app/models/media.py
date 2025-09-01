"""
Media and timeline models for video editing
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class MediaType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class MediaFile(Base, TimestampMixin):
    __tablename__ = "media_files"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # S3/MinIO path
    file_size = Column(Integer, nullable=False)  # Size in bytes
    media_type = Column(Enum(MediaType), nullable=False)
    duration = Column(Float, nullable=True)  # Duration in seconds (for video/audio)
    width = Column(Integer, nullable=True)  # Width in pixels (for video/image)
    height = Column(Integer, nullable=True)  # Height in pixels (for video/image)
    fps = Column(Float, nullable=True)  # Frames per second (for video)
    metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Relationships
    project = relationship("Project", back_populates="media_files")
    timeline_clips = relationship("TimelineClip", back_populates="media_file")
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, filename='{self.filename}', type='{self.media_type}')>"


class TimelineClip(Base, TimestampMixin):
    __tablename__ = "timeline_clips"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)
    clip_type = Column(String(50), nullable=False)  # video, audio, text, transition
    start_time = Column(Float, nullable=False)  # Start time on timeline (seconds)
    duration = Column(Float, nullable=False)  # Duration on timeline (seconds)
    media_start = Column(Float, nullable=True)  # Start time in source media (seconds)
    media_end = Column(Float, nullable=True)  # End time in source media (seconds)
    track_number = Column(Integer, nullable=False)  # Track number (0 = video, 1+ = audio)
    properties = Column(JSON, nullable=True)  # Clip properties (effects, filters, etc.)
    position = Column(JSON, nullable=True)  # Position and transform data
    
    # Relationships
    project = relationship("Project", back_populates="timeline_clips")
    media_file = relationship("MediaFile", back_populates="timeline_clips")
    
    def __repr__(self):
        return f"<TimelineClip(id={self.id}, type='{self.clip_type}', start={self.start_time})>"


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)  # text, system, mention
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, user_id={self.user_id}, message='{self.message[:50]}...')>"
