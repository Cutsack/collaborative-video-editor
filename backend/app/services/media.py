"""
Media service for S3/MinIO file operations
"""

import os
import uuid
from typing import Optional, List
from datetime import timedelta
import boto3
from minio import Minio
from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.media import MediaFile, MediaType


class MediaService:
    """Service for handling media file operations with S3/MinIO"""
    
    def __init__(self):
        self.use_minio = not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        
        if self.use_minio:
            # Use MinIO for local development
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=settings.MINIO_SECURE
            )
            self.bucket_name = "video-editor-media"
        else:
            # Use AWS S3 for production
            self.client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION
            )
            self.bucket_name = settings.AWS_S3_BUCKET
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists"""
        try:
            if self.use_minio:
                if not self.client.bucket_exists(self.bucket_name):
                    self.client.make_bucket(self.bucket_name)
            else:
                self.client.head_bucket(Bucket=self.bucket_name)
        except Exception as e:
            print(f"Warning: Could not ensure bucket exists: {e}")
    
    def generate_presigned_upload_url(self, filename: str, content_type: str, project_id: int) -> dict:
        """Generate a presigned URL for file upload"""
        file_key = f"projects/{project_id}/{uuid.uuid4()}_{filename}"
        
        try:
            if self.use_minio:
                # MinIO presigned URL
                url = self.client.presigned_put_object(
                    self.bucket_name,
                    file_key,
                    expires=timedelta(hours=1)
                )
            else:
                # AWS S3 presigned URL
                url = self.client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_key,
                        'ContentType': content_type
                    },
                    ExpiresIn=3600  # 1 hour
                )
            
            return {
                "upload_url": url,
                "file_key": file_key,
                "bucket": self.bucket_name
            }
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for file download"""
        try:
            if self.use_minio:
                return self.client.presigned_get_object(
                    self.bucket_name,
                    file_key,
                    expires=timedelta(seconds=expires_in)
                )
            else:
                return self.client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_key
                    },
                    ExpiresIn=expires_in
                )
        except Exception as e:
            raise Exception(f"Failed to generate download URL: {e}")
    
    def delete_file(self, file_key: str) -> bool:
        """Delete a file from storage"""
        try:
            if self.use_minio:
                self.client.remove_object(self.bucket_name, file_key)
            else:
                self.client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except Exception as e:
            print(f"Failed to delete file {file_key}: {e}")
            return False
    
    def get_file_info(self, file_key: str) -> Optional[dict]:
        """Get file information from storage"""
        try:
            if self.use_minio:
                stat = self.client.stat_object(self.bucket_name, file_key)
                return {
                    "size": stat.size,
                    "last_modified": stat.last_modified,
                    "etag": stat.etag
                }
            else:
                response = self.client.head_object(Bucket=self.bucket_name, Key=file_key)
                return {
                    "size": response['ContentLength'],
                    "last_modified": response['LastModified'],
                    "etag": response['ETag']
                }
        except Exception as e:
            print(f"Failed to get file info for {file_key}: {e}")
            return None


# Global media service instance
media_service = MediaService()
