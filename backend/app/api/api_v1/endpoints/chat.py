"""
Chat management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.schemas import (
    ChatMessageCreate, ChatMessageResponse
)
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.media import ChatMessage
from app.api.api_v1.endpoints.auth import get_current_user_from_token

router = APIRouter()


@router.post("/", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new chat message"""
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == message_data.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Create chat message
    message = ChatMessage(
        project_id=message_data.project_id,
        user_id=current_user.id,
        message=message_data.message,
        message_type=message_data.message_type
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


@router.get("/project/{project_id}", response_model=List[ChatMessageResponse])
async def get_project_chat_messages(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get chat messages for a project"""
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
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id
    ).order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages


@router.get("/{message_id}", response_model=ChatMessageResponse)
async def get_chat_message(
    message_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific chat message"""
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found"
        )
    
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == message.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access denied to chat message"
        )
    
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_message(
    message_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a chat message (only message author or project owner can delete)"""
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found"
        )
    
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == message.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access denied to chat message"
        )
    
    # Check if user can delete the message
    project = db.query(Project).filter(Project.id == message.project_id).first()
    can_delete = (
        message.user_id == current_user.id or  # Message author
        member.role == "owner" or              # Project owner
        (member.role == "editor" and project.owner_id == current_user.id)  # Editor with owner permissions
    )
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete message"
        )
    
    db.delete(message)
    db.commit()
    
    return None


@router.get("/project/{project_id}/unread")
async def get_unread_message_count(
    project_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get count of unread messages for current user in project"""
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
    
    # For now, return total message count
    # In a real implementation, you'd track read/unread status
    total_messages = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id
    ).count()
    
    return {
        "project_id": project_id,
        "unread_count": total_messages,  # Placeholder - implement proper read tracking
        "total_messages": total_messages
    }
