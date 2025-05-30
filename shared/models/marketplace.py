from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class AgentModel(Base):
    """Database model for marketplace agents"""
    __tablename__ = "marketplace_agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    author_id = Column(String, ForeignKey("users.id"))
    category = Column(String(100))
    tags = Column(JSON)  # List of tags
    version = Column(String(50), default="1.0.0")
    icon_url = Column(String(512))
    repository_url = Column(String(512))
    
    # Agent configuration
    agent_type = Column(String(100))  # "content_mind", "workflow", etc.
    capabilities = Column(JSON)  # List of capabilities
    requirements = Column(JSON)  # System requirements
    configuration_schema = Column(JSON)  # JSON schema for user settings
    
    # Marketplace metadata
    pricing_model = Column(String(50), default="free")  # "free", "paid", "freemium"
    price = Column(Float, default=0.0)
    license = Column(String(100), default="MIT")
    
    # Statistics
    install_count = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relationships
    installations = relationship("AgentInstallationModel", back_populates="agent", cascade="all, delete-orphan")
    reviews = relationship("AgentReviewModel", back_populates="agent", cascade="all, delete-orphan")


class AgentInstallationModel(Base):
    """Database model for agent installations by users"""
    __tablename__ = "agent_installations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    agent_id = Column(String, ForeignKey("marketplace_agents.id"), nullable=False)
    
    # Installation metadata
    installed_version = Column(String(50))
    settings = Column(JSON)  # User-specific agent settings
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("AgentModel", back_populates="installations")


class AgentReviewModel(Base):
    """Database model for agent reviews and ratings"""
    __tablename__ = "agent_reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    agent_id = Column(String, ForeignKey("marketplace_agents.id"), nullable=False)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255))
    review_text = Column(Text)
    
    # Review metadata
    helpful_count = Column(Integer, default=0)
    is_verified_purchase = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("AgentModel", back_populates="reviews")


class AgentCategoryModel(Base):
    """Database model for agent categories"""
    __tablename__ = "agent_categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(100))  # Icon identifier
    color = Column(String(7))  # Hex color
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentTagModel(Base):
    """Database model for agent tags"""
    __tablename__ = "agent_tags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # Hex color
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentAnalyticsModel(Base):
    """Database model for agent usage analytics"""
    __tablename__ = "agent_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("marketplace_agents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    
    # Event tracking
    event_type = Column(String(50), nullable=False)  # "view", "install", "uninstall", "run", etc.
    event_data = Column(JSON)  # Additional event data
    
    # Context
    user_agent = Column(String(512))
    ip_address = Column(String(45))  # IPv6 compatible
    referrer = Column(String(512))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships  
    agent = relationship("AgentModel")