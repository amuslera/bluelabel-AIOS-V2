from sqlalchemy import Column, String, BigInteger, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class FileStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileModel(Base):
    __tablename__ = "files"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID, nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size = Column(BigInteger)
    storage_path = Column(String(500))
    status = Column(Enum(FileStatus), default=FileStatus.PENDING, nullable=False)
    error_message = Column(Text)
    knowledge_id = Column(UUID)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime(timezone=True))
    metadata = Column(JSONB)