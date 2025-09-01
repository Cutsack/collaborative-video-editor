"""
Project model for video editing projects
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    settings = Column(JSON, nullable=True)  # Project settings like resolution, fps, etc.
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    media_files = relationship("MediaFile", back_populates="project")
    timeline_clips = relationship("TimelineClip", back_populates="project")
    versions = relationship("ProjectVersion", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")  # owner, editor, viewer
    permissions = Column(JSON, nullable=True)  # Specific permissions
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    
    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"


class ProjectVersion(Base, TimestampMixin):
    __tablename__ = "project_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    snapshot_data = Column(JSON, nullable=False)  # Complete project state snapshot
    
    # Relationships
    project = relationship("Project", back_populates="versions")
    
    def __repr__(self):
        return f"<ProjectVersion(project_id={self.project_id}, version={self.version_number})>"
