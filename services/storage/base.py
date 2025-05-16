"""
Base storage interface for different storage backends.
Implements RULES.md #16: Storage Hierarchy
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class StorageService(ABC):
    """Abstract base class for storage services"""
    
    @abstractmethod
    async def generate_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for uploading"""
        pass
    
    @abstractmethod
    async def generate_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for downloading"""
        pass
    
    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Upload a file directly"""
        pass
    
    @abstractmethod
    async def download_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """Download a file"""
        pass
    
    @abstractmethod
    async def delete_file(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Delete a file"""
        pass
    
    @abstractmethod
    async def file_exists(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Check if a file exists"""
        pass
    
    @abstractmethod
    async def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        limit: int = 1000
    ) -> list[Dict[str, Any]]:
        """List files in a bucket with optional prefix"""
        pass
    
    @abstractmethod
    async def get_file_metadata(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """Get file metadata"""
        pass
    
    def get_storage_path(
        self,
        tenant_id: str,
        file_id: str,
        filename: str,
        category: str = "uploads"
    ) -> str:
        """
        Generate a consistent storage path.
        Format: {category}/{tenant_id}/{file_id}/{filename}
        """
        return f"{category}/{tenant_id}/{file_id}/{filename}"