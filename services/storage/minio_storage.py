"""
MinIO storage implementation for development.
Implements RULES.md #16: Storage Hierarchy
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from services.storage.base import StorageService
from core.config import get_settings


class MinIOStorage(StorageService):
    """MinIO storage implementation using S3-compatible API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.endpoint_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        
        # Create S3 client
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='us-east-1'  # Required for boto3
        )
        
        # Ensure default buckets exist
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Create default buckets if they don't exist"""
        default_buckets = ["uploads", "processed", "thumbnails", "digests"]
        
        for bucket in default_buckets:
            try:
                self.client.head_bucket(Bucket=bucket)
            except ClientError:
                self.client.create_bucket(Bucket=bucket)
    
    async def generate_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for uploading"""
        params = {
            'Bucket': bucket,
            'Key': key
        }
        
        if content_type:
            params['ContentType'] = content_type
        
        if metadata:
            params['Metadata'] = metadata
        
        url = self.client.generate_presigned_url(
            'put_object',
            Params=params,
            ExpiresIn=expires_in
        )
        
        return url
    
    async def generate_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for downloading"""
        url = self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in
        )
        
        return url
    
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Upload a file directly"""
        try:
            kwargs = {
                'Bucket': bucket,
                'Key': key,
                'Body': file_data
            }
            
            if content_type:
                kwargs['ContentType'] = content_type
            
            if metadata:
                kwargs['Metadata'] = metadata
            
            self.client.put_object(**kwargs)
            return True
        except ClientError:
            return False
    
    async def download_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """Download a file"""
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    
    async def delete_file(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Delete a file"""
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
    
    async def file_exists(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Check if a file exists"""
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
    
    async def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        limit: int = 1000
    ) -> list[Dict[str, Any]]:
        """List files in a bucket with optional prefix"""
        params = {
            'Bucket': bucket,
            'MaxKeys': limit
        }
        
        if prefix:
            params['Prefix'] = prefix
        
        response = self.client.list_objects_v2(**params)
        
        files = []
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'],
                'etag': obj['ETag']
            })
        
        return files
    
    async def get_file_metadata(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """Get file metadata"""
        response = self.client.head_object(Bucket=bucket, Key=key)
        
        return {
            'size': response['ContentLength'],
            'content_type': response.get('ContentType'),
            'last_modified': response['LastModified'],
            'etag': response['ETag'],
            'metadata': response.get('Metadata', {})
        }