from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import List, Optional, Dict, Any
import math
from datetime import datetime, timedelta

from apps.api.dependencies.database import get_db
from apps.api.dependencies.auth import get_current_user, get_optional_current_user
from shared.schemas.base import User
from shared.schemas.marketplace import (
    Agent, AgentCreate, AgentUpdate, AgentSummary, AgentListResponse,
    AgentInstallation, AgentInstallationCreate, AgentInstallationUpdate, AgentInstallationListResponse,
    AgentReview, AgentReviewCreate, AgentReviewUpdate, AgentReviewListResponse,
    AgentCategory, AgentCategoryCreate, CategoryListResponse, CategoryStatsResponse,
    AgentSearchRequest, AgentSearchFilters, SortOption, PricingModel,
    AgentAnalyticsCreate, AgentStats, MarketplaceStats,
    EventType
)
from shared.models.marketplace import (
    AgentModel, AgentInstallationModel, AgentReviewModel, 
    AgentCategoryModel, AgentTagModel, AgentAnalyticsModel
)
from core.cache import cache, cache_manager, CacheInvalidator
from core.database_optimization import profile_db_operation, QueryOptimizer
from shared.utils.pagination import Paginator, PaginationParams

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# Utility functions
def calculate_trending_score(agent: AgentModel) -> float:
    """Calculate trending score based on recent activity"""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Factors: recent installs (50%), recent views (30%), rating (20%)
    recent_installs = sum(1 for install in agent.installations 
                         if install.installed_at >= week_ago)
    recent_views = agent.view_count  # Simplified - would track recent views in production
    rating_score = agent.rating_average / 5.0
    
    return (recent_installs * 0.5) + (min(recent_views, 100) * 0.003) + (rating_score * 0.2)


def apply_search_filters(query, filters: Optional[AgentSearchFilters]) -> Any:
    """Apply search filters to SQLAlchemy query"""
    if not filters:
        return query
    
    if filters.category:
        query = query.filter(AgentModel.category == filters.category)
    
    if filters.tags:
        # Filter agents that have any of the specified tags
        tag_conditions = [func.json_extract(AgentModel.tags, f'$[*]').like(f'%{tag}%') 
                         for tag in filters.tags]
        query = query.filter(or_(*tag_conditions))
    
    if filters.pricing_model:
        query = query.filter(AgentModel.pricing_model == filters.pricing_model.value)
    
    if filters.min_rating is not None:
        query = query.filter(AgentModel.rating_average >= filters.min_rating)
    
    if filters.is_verified is not None:
        query = query.filter(AgentModel.is_verified == filters.is_verified)
    
    if filters.is_featured is not None:
        query = query.filter(AgentModel.is_featured == filters.is_featured)
    
    return query


def apply_sorting(query, sort: SortOption) -> Any:
    """Apply sorting to SQLAlchemy query"""
    if sort == SortOption.POPULAR:
        return query.order_by(desc(AgentModel.install_count))
    elif sort == SortOption.RECENT:
        return query.order_by(desc(AgentModel.created_at))
    elif sort == SortOption.RATING:
        return query.order_by(desc(AgentModel.rating_average), desc(AgentModel.rating_count))
    elif sort == SortOption.NAME:
        return query.order_by(asc(AgentModel.name))
    elif sort == SortOption.INSTALLS:
        return query.order_by(desc(AgentModel.install_count))
    else:
        return query.order_by(desc(AgentModel.install_count))


# Marketplace overview endpoints
@router.get("/stats", response_model=MarketplaceStats)
@cache(ttl=600)  # Cache for 10 minutes
@profile_db_operation
async def get_marketplace_stats(db: Session = Depends(get_db)):
    """Get marketplace overview statistics"""
    
    # Basic stats - optimized queries
    total_agents = db.query(func.count(AgentModel.id)).filter(AgentModel.is_active == True).scalar()
    total_installs = db.query(func.sum(AgentModel.install_count)).scalar() or 0
    total_categories = db.query(func.count(AgentCategoryModel.id)).filter(AgentCategoryModel.is_active == True).scalar()
    
    # Featured agents
    featured_agents = db.query(AgentModel).filter(
        and_(AgentModel.is_featured == True, AgentModel.is_active == True)
    ).limit(6).all()
    
    # Trending agents (top by recent activity)
    trending_agents = db.query(AgentModel).filter(
        AgentModel.is_active == True
    ).order_by(desc(AgentModel.install_count)).limit(6).all()
    
    # Popular categories
    popular_categories = db.query(
        AgentModel.category,
        func.count(AgentModel.id).label('count')
    ).filter(AgentModel.is_active == True).group_by(
        AgentModel.category
    ).order_by(desc('count')).limit(5).all()
    
    return MarketplaceStats(
        total_agents=total_agents,
        total_installs=total_installs,
        total_categories=total_categories,
        featured_agents=featured_agents,
        trending_agents=trending_agents,
        popular_categories=[
            {"name": cat[0], "count": cat[1]} 
            for cat in popular_categories if cat[0]
        ]
    )


# Agent listing endpoints
@router.get("/agents", response_model=AgentListResponse)
@profile_db_operation
async def list_agents(
    category: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    search: Optional[str] = None,
    sort: SortOption = SortOption.POPULAR,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List marketplace agents with filtering and pagination"""
    
    # Generate cache key for common queries
    cache_key = None
    if not search and not tags and page == 1 and limit == 20:
        cache_key = f"agents:list:{category or 'all'}:{sort.value}"
        cached = cache_manager.get(cache_key)
        if cached:
            return AgentListResponse(**cached)
    
    # Base query with eager loading
    query = db.query(AgentModel).options(
        selectinload(AgentModel.installations),
        selectinload(AgentModel.reviews)
    ).filter(AgentModel.is_active == True)
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            AgentModel.name.ilike(search_term),
            AgentModel.description.ilike(search_term),
            func.json_extract(AgentModel.capabilities, '$[*]').like(search_term)
        ))
    
    # Apply filters
    filters = AgentSearchFilters(
        category=category,
        tags=tags.split(',') if tags else None
    )
    query = apply_search_filters(query, filters)
    
    # Apply sorting
    query = apply_sorting(query, sort)
    
    # Use optimized pagination
    paginator = Paginator()
    result = paginator.paginate(
        query=query,
        page=page,
        per_page=limit,
        max_per_page=100
    )
    
    response = AgentListResponse(
        agents=result["items"],
        total=result["total"],
        page=result["page"],
        pages=result["pages"],
        limit=result["per_page"]
    )
    
    # Cache common queries
    if cache_key:
        cache_manager.set(cache_key, response.dict(), ttl=300)
    
    return response


@router.post("/agents/search", response_model=AgentListResponse)
async def search_agents(
    search_request: AgentSearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Advanced agent search with complex filters"""
    
    # Base query
    query = db.query(AgentModel).filter(AgentModel.is_active == True)
    
    # Apply text search
    if search_request.query:
        search_term = f"%{search_request.query}%"
        query = query.filter(or_(
            AgentModel.name.ilike(search_term),
            AgentModel.description.ilike(search_term),
            func.json_extract(AgentModel.capabilities, '$[*]').like(search_term),
            func.json_extract(AgentModel.tags, '$[*]').like(search_term)
        ))
    
    # Apply filters
    query = apply_search_filters(query, search_request.filters)
    
    # Apply sorting
    query = apply_sorting(query, search_request.sort)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (search_request.page - 1) * search_request.limit
    agents = query.offset(offset).limit(search_request.limit).all()
    
    # Calculate pages
    pages = math.ceil(total / search_request.limit)
    
    return AgentListResponse(
        agents=agents,
        total=total,
        page=search_request.page,
        pages=pages,
        limit=search_request.limit
    )


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent_details(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get detailed information about a specific agent"""
    
    # Get agent
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent or not agent.is_active:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Increment view count
    agent.view_count += 1
    db.commit()
    
    # Track analytics
    if current_user:
        analytics = AgentAnalyticsModel(
            agent_id=agent_id,
            user_id=current_user.id,
            event_type=EventType.VIEW.value
        )
        db.add(analytics)
        db.commit()
    
    # Convert to response model
    agent_data = Agent.from_orm(agent)
    
    # Add user-specific fields if authenticated
    if current_user:
        # Check if user has installed this agent
        installation = db.query(AgentInstallationModel).filter(
            and_(
                AgentInstallationModel.user_id == current_user.id,
                AgentInstallationModel.agent_id == agent_id,
                AgentInstallationModel.is_active == True
            )
        ).first()
        agent_data.user_installed = installation is not None
        
        # Check user's rating for this agent
        review = db.query(AgentReviewModel).filter(
            and_(
                AgentReviewModel.user_id == current_user.id,
                AgentReviewModel.agent_id == agent_id
            )
        ).first()
        agent_data.user_rating = review.rating if review else None
    
    return agent_data


# Agent installation endpoints
@router.post("/agents/{agent_id}/install", response_model=AgentInstallation)
async def install_agent(
    agent_id: str,
    installation_data: AgentInstallationCreate = AgentInstallationCreate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Install an agent for the current user"""
    
    # Check if agent exists and is active
    agent = db.query(AgentModel).filter(
        and_(AgentModel.id == agent_id, AgentModel.is_active == True)
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if already installed
    existing_installation = db.query(AgentInstallationModel).filter(
        and_(
            AgentInstallationModel.user_id == current_user.id,
            AgentInstallationModel.agent_id == agent_id,
            AgentInstallationModel.is_active == True
        )
    ).first()
    
    if existing_installation:
        raise HTTPException(status_code=400, detail="Agent already installed")
    
    # Create installation
    installation = AgentInstallationModel(
        user_id=current_user.id,
        agent_id=agent_id,
        installed_version=agent.version,
        settings=installation_data.settings
    )
    db.add(installation)
    
    # Update agent install count
    agent.install_count += 1
    
    # Track analytics
    analytics = AgentAnalyticsModel(
        agent_id=agent_id,
        user_id=current_user.id,
        event_type=EventType.INSTALL.value
    )
    db.add(analytics)
    
    db.commit()
    db.refresh(installation)
    
    # Load agent details for response
    installation_with_agent = db.query(AgentInstallationModel).options(
        joinedload(AgentInstallationModel.agent)
    ).filter(AgentInstallationModel.id == installation.id).first()
    
    return installation_with_agent


@router.delete("/agents/{agent_id}/install")
async def uninstall_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uninstall an agent for the current user"""
    
    # Find installation
    installation = db.query(AgentInstallationModel).filter(
        and_(
            AgentInstallationModel.user_id == current_user.id,
            AgentInstallationModel.agent_id == agent_id,
            AgentInstallationModel.is_active == True
        )
    ).first()
    
    if not installation:
        raise HTTPException(status_code=404, detail="Agent not installed")
    
    # Deactivate installation (soft delete)
    installation.is_active = False
    
    # Update agent install count
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if agent and agent.install_count > 0:
        agent.install_count -= 1
    
    # Track analytics
    analytics = AgentAnalyticsModel(
        agent_id=agent_id,
        user_id=current_user.id,
        event_type=EventType.UNINSTALL.value
    )
    db.add(analytics)
    
    db.commit()
    
    return {"message": "Agent uninstalled successfully"}


@router.get("/my-agents", response_model=AgentInstallationListResponse)
async def get_my_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of agents installed by the current user"""
    
    installations = db.query(AgentInstallationModel).options(
        joinedload(AgentInstallationModel.agent)
    ).filter(
        and_(
            AgentInstallationModel.user_id == current_user.id,
            AgentInstallationModel.is_active == True
        )
    ).order_by(desc(AgentInstallationModel.installed_at)).all()
    
    return AgentInstallationListResponse(
        installations=installations,
        total=len(installations)
    )


# Review endpoints
@router.post("/agents/{agent_id}/reviews", response_model=AgentReview)
async def create_review(
    agent_id: str,
    review_data: AgentReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update a review for an agent"""
    
    # Check if agent exists
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent or not agent.is_active:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if user has already reviewed this agent
    existing_review = db.query(AgentReviewModel).filter(
        and_(
            AgentReviewModel.user_id == current_user.id,
            AgentReviewModel.agent_id == agent_id
        )
    ).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = review_data.rating
        existing_review.title = review_data.title
        existing_review.review_text = review_data.review_text
        existing_review.updated_at = datetime.utcnow()
        review = existing_review
    else:
        # Create new review
        review = AgentReviewModel(
            user_id=current_user.id,
            agent_id=agent_id,
            rating=review_data.rating,
            title=review_data.title,
            review_text=review_data.review_text
        )
        db.add(review)
        agent.rating_count += 1
    
    # Recalculate agent rating
    all_reviews = db.query(AgentReviewModel).filter(
        AgentReviewModel.agent_id == agent_id
    ).all()
    if all_reviews:
        agent.rating_average = sum(r.rating for r in all_reviews) / len(all_reviews)
        agent.rating_count = len(all_reviews)
    
    # Track analytics
    analytics = AgentAnalyticsModel(
        agent_id=agent_id,
        user_id=current_user.id,
        event_type=EventType.RATE.value,
        event_data={"rating": review_data.rating}
    )
    db.add(analytics)
    
    db.commit()
    db.refresh(review)
    
    return review


@router.get("/agents/{agent_id}/reviews", response_model=AgentReviewListResponse)
async def get_agent_reviews(
    agent_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get reviews for a specific agent"""
    
    # Check if agent exists
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent or not agent.is_active:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get reviews with pagination
    query = db.query(AgentReviewModel).filter(
        AgentReviewModel.agent_id == agent_id
    ).order_by(desc(AgentReviewModel.created_at))
    
    total = query.count()
    offset = (page - 1) * limit
    reviews = query.offset(offset).limit(limit).all()
    pages = math.ceil(total / limit)
    
    return AgentReviewListResponse(
        reviews=reviews,
        total=total,
        page=page,
        pages=pages,
        limit=limit
    )


# Category endpoints
@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(db: Session = Depends(get_db)):
    """Get list of agent categories"""
    
    categories = db.query(AgentCategoryModel).filter(
        AgentCategoryModel.is_active == True
    ).order_by(AgentCategoryModel.sort_order, AgentCategoryModel.display_name).all()
    
    return CategoryListResponse(categories=categories)


@router.get("/categories/stats", response_model=CategoryStatsResponse)
async def get_category_stats(db: Session = Depends(get_db)):
    """Get category statistics (agent count per category)"""
    
    stats = db.query(
        AgentModel.category,
        func.count(AgentModel.id).label('count')
    ).filter(
        AgentModel.is_active == True
    ).group_by(AgentModel.category).all()
    
    # Include category details
    categories_data = []
    for category_name, count in stats:
        if category_name:
            category = db.query(AgentCategoryModel).filter(
                AgentCategoryModel.name == category_name
            ).first()
            categories_data.append({
                "id": category.id if category else category_name,
                "name": category_name,
                "display_name": category.display_name if category else category_name,
                "count": count
            })
    
    return CategoryStatsResponse(categories=categories_data)


# Analytics endpoints (optional - for agent creators)
@router.get("/agents/{agent_id}/stats", response_model=AgentStats)
async def get_agent_stats(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific agent (for agent creators)"""
    
    # Check if agent exists and user owns it
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # For MVP, allow any authenticated user to view stats
    # In production, check if current_user.id == agent.author_id
    
    # Calculate recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_analytics = db.query(AgentAnalyticsModel).filter(
        and_(
            AgentAnalyticsModel.agent_id == agent_id,
            AgentAnalyticsModel.created_at >= thirty_days_ago
        )
    ).all()
    
    # Group by event type
    recent_activity = {}
    for event_type in EventType:
        recent_activity[event_type.value] = sum(
            1 for a in recent_analytics if a.event_type == event_type.value
        )
    
    # Get active installations
    active_installs = db.query(AgentInstallationModel).filter(
        and_(
            AgentInstallationModel.agent_id == agent_id,
            AgentInstallationModel.is_active == True
        )
    ).count()
    
    return AgentStats(
        total_views=agent.view_count,
        total_installs=agent.install_count,
        active_installs=active_installs,
        average_rating=agent.rating_average,
        total_reviews=agent.rating_count,
        recent_activity=recent_activity
    )