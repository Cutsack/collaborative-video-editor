"""
User model for authentication and user management
"""

from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(Text, nullable=True)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
