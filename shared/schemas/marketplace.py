from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class PricingModel(str, Enum):
    """Pricing models for agents"""
    FREE = "free"
    PAID = "paid"
    FREEMIUM = "freemium"


class SortOption(str, Enum):
    """Sort options for agent listings"""
    POPULAR = "popular"
    RECENT = "recent"
    RATING = "rating"
    NAME = "name"
    INSTALLS = "installs"


class EventType(str, Enum):
    """Analytics event types"""
    VIEW = "view"
    INSTALL = "install"
    UNINSTALL = "uninstall"
    RUN = "run"
    RATE = "rate"
    REVIEW = "review"


# Base schemas
class AgentCategoryBase(BaseModel):
    """Base schema for agent categories"""
    name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0


class AgentCategoryCreate(AgentCategoryBase):
    """Schema for creating agent categories"""
    pass


class AgentCategory(AgentCategoryBase):
    """Schema for agent category responses"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class AgentTagBase(BaseModel):
    """Base schema for agent tags"""
    name: str
    display_name: str
    description: Optional[str] = None
    color: Optional[str] = None


class AgentTagCreate(AgentTagBase):
    """Schema for creating agent tags"""
    pass


class AgentTag(AgentTagBase):
    """Schema for agent tag responses"""
    id: str
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Agent schemas
class AgentBase(BaseModel):
    """Base schema for marketplace agents"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    icon_url: Optional[str] = None
    repository_url: Optional[str] = None
    agent_type: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    configuration_schema: Dict[str, Any] = Field(default_factory=dict)
    pricing_model: PricingModel = PricingModel.FREE
    price: float = 0.0
    license: str = "MIT"


class AgentCreate(AgentBase):
    """Schema for creating agents"""
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('pricing_model') == PricingModel.FREE and v > 0:
            raise ValueError('Free agents cannot have a price')
        if values.get('pricing_model') == PricingModel.PAID and v <= 0:
            raise ValueError('Paid agents must have a price > 0')
        return v


class AgentUpdate(BaseModel):
    """Schema for updating agents"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    icon_url: Optional[str] = None
    repository_url: Optional[str] = None
    capabilities: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None
    configuration_schema: Optional[Dict[str, Any]] = None
    pricing_model: Optional[PricingModel] = None
    price: Optional[float] = None
    license: Optional[str] = None


class Agent(AgentBase):
    """Schema for agent responses"""
    id: str
    author_id: str
    install_count: int
    rating_average: float
    rating_count: int
    view_count: int
    is_active: bool
    is_verified: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    # Additional fields for detailed view
    user_installed: Optional[bool] = None
    user_rating: Optional[int] = None
    
    class Config:
        orm_mode = True


class AgentSummary(BaseModel):
    """Schema for agent list responses (lighter version)"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str]
    version: str
    icon_url: Optional[str] = None
    capabilities: List[str]
    pricing_model: PricingModel
    price: float
    install_count: int
    rating_average: float
    rating_count: int
    is_featured: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


# Installation schemas
class AgentInstallationBase(BaseModel):
    """Base schema for agent installations"""
    settings: Dict[str, Any] = Field(default_factory=dict)


class AgentInstallationCreate(AgentInstallationBase):
    """Schema for creating agent installations"""
    pass


class AgentInstallationUpdate(BaseModel):
    """Schema for updating agent installations"""
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentInstallation(AgentInstallationBase):
    """Schema for agent installation responses"""
    id: str
    user_id: str
    agent_id: str
    installed_version: Optional[str] = None
    is_active: bool
    last_used: Optional[datetime] = None
    usage_count: int
    installed_at: datetime
    updated_at: datetime
    
    # Include agent details
    agent: Optional[AgentSummary] = None
    
    class Config:
        orm_mode = True


# Review schemas
class AgentReviewBase(BaseModel):
    """Base schema for agent reviews"""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    review_text: Optional[str] = None


class AgentReviewCreate(AgentReviewBase):
    """Schema for creating agent reviews"""
    pass


class AgentReviewUpdate(BaseModel):
    """Schema for updating agent reviews"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    review_text: Optional[str] = None


class AgentReview(AgentReviewBase):
    """Schema for agent review responses"""
    id: str
    user_id: str
    agent_id: str
    helpful_count: int
    is_verified_purchase: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# List response schemas
class AgentListResponse(BaseModel):
    """Schema for paginated agent list responses"""
    agents: List[AgentSummary]
    total: int
    page: int
    pages: int
    limit: int


class AgentInstallationListResponse(BaseModel):
    """Schema for user's installed agents response"""
    installations: List[AgentInstallation]
    total: int


class AgentReviewListResponse(BaseModel):
    """Schema for agent reviews list response"""
    reviews: List[AgentReview]
    total: int
    page: int
    pages: int
    limit: int


class CategoryListResponse(BaseModel):
    """Schema for categories list response"""
    categories: List[AgentCategory]


class CategoryStatsResponse(BaseModel):
    """Schema for category stats response"""
    categories: List[Dict[str, Any]]  # {id, name, display_name, count}


# Search and filter schemas
class AgentSearchFilters(BaseModel):
    """Schema for agent search filters"""
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    pricing_model: Optional[PricingModel] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    is_verified: Optional[bool] = None
    is_featured: Optional[bool] = None


class AgentSearchRequest(BaseModel):
    """Schema for agent search requests"""
    query: Optional[str] = None
    filters: Optional[AgentSearchFilters] = None
    sort: SortOption = SortOption.POPULAR
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


# Analytics schemas
class AgentAnalyticsCreate(BaseModel):
    """Schema for creating analytics events"""
    agent_id: str
    event_type: EventType
    event_data: Dict[str, Any] = Field(default_factory=dict)
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referrer: Optional[str] = None


class AgentStats(BaseModel):
    """Schema for agent statistics"""
    total_views: int
    total_installs: int
    active_installs: int
    average_rating: float
    total_reviews: int
    recent_activity: Dict[str, int]  # Last 30 days activity by event type


# Marketplace overview schemas
class MarketplaceStats(BaseModel):
    """Schema for marketplace overview statistics"""
    total_agents: int
    total_installs: int
    total_categories: int
    featured_agents: List[AgentSummary]
    trending_agents: List[AgentSummary]
    popular_categories: List[Dict[str, Any]]