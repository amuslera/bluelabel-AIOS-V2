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
    # For MVP, we'll create a mock user
    # TODO: Implement proper JWT validation
    return User(
        id=str(uuid.uuid4()),
        email="ariel@example.com",
        tenant_id=str(uuid.uuid4())
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