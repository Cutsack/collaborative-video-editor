"""
Base models and common fields
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin to add timestamp fields to models"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(String(1), default='N', nullable=False)  # Y/N flag
