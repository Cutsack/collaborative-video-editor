"""
Timeline management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.schemas import (
    TimelineClipCreate, TimelineClipUpdate, TimelineClipResponse
)
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.media import TimelineClip
from app.api.api_v1.endpoints.auth import get_current_user_from_token

router = APIRouter()


@router.post("/", response_model=TimelineClipResponse, status_code=status.HTTP_201_CREATED)
async def create_timeline_clip(
    clip_data: TimelineClipCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new timeline clip"""
    # Check if user has editor permissions
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == clip_data.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit timeline"
        )
    
    # Create timeline clip
    clip = TimelineClip(
        project_id=clip_data.project_id,
        media_file_id=clip_data.media_file_id,
        clip_type=clip_data.clip_type,
        start_time=clip_data.start_time,
        duration=clip_data.duration,
        media_start=clip_data.media_start,
        media_end=clip_data.media_end,
        track_number=clip_data.track_number,
        properties=clip_data.properties,
        position=clip_data.position
    )
    
    db.add(clip)
    db.commit()
    db.refresh(clip)
    
    return clip


@router.get("/project/{project_id}", response_model=List[TimelineClipResponse])
async def get_project_timeline(
    project_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all timeline clips for a project"""
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
    
    clips = db.query(TimelineClip).filter(
        TimelineClip.project_id == project_id
    ).order_by(TimelineClip.track_number, TimelineClip.start_time).all()
    
    return clips


@router.get("/{clip_id}", response_model=TimelineClipResponse)
async def get_timeline_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific timeline clip"""
    clip = db.query(TimelineClip).filter(TimelineClip.id == clip_id).first()
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline clip not found"
        )
    
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == clip.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access denied to timeline clip"
        )
    
    return clip


@router.put("/{clip_id}", response_model=TimelineClipResponse)
async def update_timeline_clip(
    clip_id: int,
    clip_data: TimelineClipUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a timeline clip"""
    clip = db.query(TimelineClip).filter(TimelineClip.id == clip_id).first()
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline clip not found"
        )
    
    # Check if user has editor permissions
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == clip.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit timeline"
        )
    
    # Update clip fields
    update_data = clip_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clip, field, value)
    
    db.commit()
    db.refresh(clip)
    
    return clip


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeline_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a timeline clip"""
    clip = db.query(TimelineClip).filter(TimelineClip.id == clip_id).first()
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline clip not found"
        )
    
    # Check if user has editor permissions
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == clip.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit timeline"
        )
    
    db.delete(clip)
    db.commit()
    
    return None


@router.post("/project/{project_id}/reorder")
async def reorder_timeline_clips(
    project_id: int,
    clip_order: List[int],  # List of clip IDs in new order
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Reorder timeline clips for a project"""
    # Check if user has editor permissions
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit timeline"
        )
    
    # Update clip positions based on new order
    for index, clip_id in enumerate(clip_order):
        clip = db.query(TimelineClip).filter(
            TimelineClip.id == clip_id,
            TimelineClip.project_id == project_id
        ).first()
        
        if clip:
            clip.start_time = index * 1.0  # Simple sequential ordering
            # You might want to implement more sophisticated ordering logic
    
    db.commit()
    
    return {"message": "Timeline reordered successfully"}
