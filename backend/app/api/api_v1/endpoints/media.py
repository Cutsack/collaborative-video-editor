"""
Media management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.schemas import UploadRequest, UploadResponse, MediaFileResponse
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.media import MediaFile, MediaType
from app.services.media import media_service
from app.api.api_v1.endpoints.auth import get_current_user_from_token
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def get_upload_url(
    upload_data: UploadRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get presigned URL for file upload"""
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == upload_data.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Validate file size
    max_size = int(settings.MAX_FILE_SIZE.replace("MB", "")) * 1024 * 1024
    if upload_data.file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE}"
        )
    
    # Validate file type
    file_extension = upload_data.filename.split(".")[-1].lower()
    allowed_formats = []
    
    if upload_data.content_type.startswith("video/"):
        allowed_formats = settings.ALLOWED_VIDEO_FORMATS
    elif upload_data.content_type.startswith("audio/"):
        allowed_formats = settings.ALLOWED_AUDIO_FORMATS
    elif upload_data.content_type.startswith("image/"):
        allowed_formats = settings.ALLOWED_IMAGE_FORMATS
    
    if file_extension not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed formats: {', '.join(allowed_formats)}"
        )
    
    # Generate presigned upload URL
    try:
        upload_info = media_service.generate_presigned_upload_url(
            filename=upload_data.filename,
            content_type=upload_data.content_type,
            project_id=upload_data.project_id
        )
        return upload_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.post("/confirm", response_model=MediaFileResponse)
async def confirm_upload(
    filename: str,
    file_key: str,
    project_id: int,
    content_type: str,
    file_size: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Confirm file upload and create media file record"""
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
    
    # Determine media type from content type
    if content_type.startswith("video/"):
        media_type = MediaType.VIDEO
    elif content_type.startswith("audio/"):
        media_type = MediaType.AUDIO
    elif content_type.startswith("image/"):
        media_type = MediaType.IMAGE
    else:
        media_type = MediaType.VIDEO  # Default fallback
    
    # Create media file record
    media_file = MediaFile(
        project_id=project_id,
        filename=filename,
        original_filename=filename,
        file_path=file_key,
        file_size=file_size,
        media_type=media_type,
        # Note: duration, width, height, fps will be extracted later
        # or can be updated via separate endpoint
    )
    
    db.add(media_file)
    db.commit()
    db.refresh(media_file)
    
    return media_file


@router.get("/{media_id}", response_model=MediaFileResponse)
async def get_media_file(
    media_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get media file details"""
    media_file = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == media_file.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access denied to media file"
        )
    
    return media_file


@router.get("/{media_id}/download")
async def get_download_url(
    media_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get presigned download URL for media file"""
    media_file = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Check if user has access to project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == media_file.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access denied to media file"
        )
    
    try:
        download_url = media_service.get_file_url(media_file.file_path)
        return {"download_url": download_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_file(
    media_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a media file"""
    media_file = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Check if user has editor permissions
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == media_file.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete media file"
        )
    
    # Delete from storage
    try:
        media_service.delete_file(media_file.file_path)
    except Exception as e:
        print(f"Warning: Failed to delete file from storage: {e}")
    
    # Delete from database
    db.delete(media_file)
    db.commit()
    
    return None
