"""
Setup endpoint for testing
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from apps.api.dependencies.database import get_db

router = APIRouter(prefix="/api/v1/setup", tags=["setup"])


@router.post("/test-user")
async def create_test_user(db: Session = Depends(get_db)):
    """
    Create a test user for development
    """
    try:
        # Check if user already exists
        existing = db.execute(
            text("SELECT id FROM users WHERE id = :user_id"),
            {"user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}
        ).first()
        
        if existing:
            return {"message": "Test user already exists"}
        
        # Create user
        db.execute(
            text("""
            INSERT INTO users (id, email, tenant_id, created_at)
            VALUES (:id, :email, :tenant_id, :created_at)
            """),
            {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "email": "ariel@example.com",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": datetime.utcnow()
            }
        )
        db.commit()
        
        return {"message": "Test user created successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}