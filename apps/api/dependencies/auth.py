from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.schemas.base import User
from typing import Optional
import uuid

# Security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> User:
    """
    Dependency to get the current authenticated user.
    
    For MVP, we'll create a mock user. In production, this would:
    1. Validate the JWT token
    2. Extract user claims
    3. Return User object with proper tenant_id
    """
    # For MVP, we'll use a fixed user ID for testing
    # TODO: Implement proper JWT validation
    return User(
        id="f47ac10b-58cc-4372-a567-0e02b2c3d479",  # Fixed UUID for testing
        email="ariel@example.com",
        tenant_id="550e8400-e29b-41d4-a716-446655440000"  # Fixed tenant ID
    )

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional authentication dependency.
    """
    if not credentials:
        return None
    return get_current_user(credentials)