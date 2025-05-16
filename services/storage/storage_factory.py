"""
Storage service factory for selecting appropriate backend.
"""
import os
from services.storage.base import StorageService
from services.storage.minio_storage import MinIOStorage


def get_storage_service() -> StorageService:
    """
    Factory function to get the appropriate storage service.
    
    Returns storage service based on STORAGE_BACKEND environment variable:
    - "minio": MinIO for development
    - "s3": AWS S3 for production (to be implemented)
    - "r2": Cloudflare R2 for production (to be implemented)
    """
    backend = os.getenv("STORAGE_BACKEND", "minio").lower()
    
    if backend == "minio":
        return MinIOStorage()
    elif backend == "s3":
        # TODO: Implement S3Storage
        raise NotImplementedError("S3 storage not yet implemented")
    elif backend == "r2":
        # TODO: Implement R2Storage
        raise NotImplementedError("R2 storage not yet implemented")
    else:
        raise ValueError(f"Unknown storage backend: {backend}")


# Dependency injection helper for FastAPI
async def get_storage() -> StorageService:
    """Dependency injection function for FastAPI"""
    return get_storage_service()