"""
Project management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
)
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.api.api_v1.endpoints.auth import get_current_user_from_token

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id,
        is_public=project_data.is_public,
        settings=project_data.settings
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Add owner as project member with editor role
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)
    db.commit()
    
    return project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List projects accessible to current user"""
    # Get projects where user is owner or member
    projects_query = db.query(Project).join(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    )
    
    total = projects_query.count()
    projects = projects_query.offset(skip).limit(limit).all()
    
    return ProjectListResponse(projects=projects, total=total)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get project details"""
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update project details"""
    # Check if user is owner or has editor permissions
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit project"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update project fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a project (only owner can delete)"""
    # Check if user is owner
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete project"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    return None


@router.post("/{project_id}/members")
async def add_project_member(
    project_id: int,
    user_id: int,
    role: str = "viewer",
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Add a member to a project"""
    # Check if current user is owner or editor
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage project members"
        )
    
    # Check if user is already a member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a project member"
        )
    
    # Add new member
    new_member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role
    )
    
    db.add(new_member)
    db.commit()
    
    return {"message": "Member added successfully"}
