"""
Optimized pagination utilities for API endpoints.
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Query
from sqlalchemy import func
import math

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100
    
    def validate_params(self):
        """Validate and adjust pagination parameters"""
        self.page = max(1, self.page)
        self.per_page = min(max(1, self.per_page), self.max_per_page)
        return self
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model"""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        arbitrary_types_allowed = True


class Paginator:
    """Optimized paginator for SQLAlchemy queries"""
    
    @staticmethod
    def paginate(
        query: Query,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100,
        count_query: Optional[Query] = None
    ) -> Dict[str, Any]:
        """
        Paginate a SQLAlchemy query with optimized counting.
        
        Args:
            query: The query to paginate
            page: Current page number
            per_page: Items per page
            max_per_page: Maximum allowed items per page
            count_query: Optional optimized count query
        
        Returns:
            Dictionary with pagination data
        """
        # Validate parameters
        page = max(1, page)
        per_page = min(max(1, per_page), max_per_page)
        offset = (page - 1) * per_page
        
        # Get items for current page
        items = query.limit(per_page).offset(offset).all()
        
        # Get total count using optimized query if provided
        if count_query:
            total = count_query.scalar()
        else:
            # Remove ordering and limits for count query
            total = query.order_by(None).offset(None).limit(None).count()
        
        # Calculate pagination metadata
        pages = math.ceil(total / per_page) if total > 0 else 1
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    
    @staticmethod
    def get_pagination_links(
        base_url: str,
        page: int,
        pages: int,
        **params
    ) -> Dict[str, Optional[str]]:
        """Generate pagination links for API responses"""
        links = {
            "self": f"{base_url}?page={page}",
            "first": f"{base_url}?page=1",
            "last": f"{base_url}?page={pages}",
            "next": None,
            "prev": None
        }
        
        # Add query parameters
        for key, value in params.items():
            for link_key in links:
                if links[link_key]:
                    links[link_key] += f"&{key}={value}"
        
        # Add next/prev links if applicable
        if page < pages:
            links["next"] = f"{base_url}?page={page + 1}"
            for key, value in params.items():
                links["next"] += f"&{key}={value}"
        
        if page > 1:
            links["prev"] = f"{base_url}?page={page - 1}"
            for key, value in params.items():
                links["prev"] += f"&{key}={value}"
        
        return links


class CursorPaginator:
    """Cursor-based pagination for improved performance on large datasets"""
    
    @staticmethod
    def paginate_by_cursor(
        query: Query,
        cursor_field: str,
        cursor_value: Optional[Any] = None,
        limit: int = 20,
        direction: str = "next"
    ) -> Dict[str, Any]:
        """
        Paginate using cursor-based pagination.
        More efficient for large datasets than offset-based pagination.
        """
        if cursor_value:
            if direction == "next":
                query = query.filter(
                    getattr(query.column_descriptions[0]['type'], cursor_field) > cursor_value
                )
            else:
                query = query.filter(
                    getattr(query.column_descriptions[0]['type'], cursor_field) < cursor_value
                )
                query = query.order_by(
                    getattr(query.column_descriptions[0]['type'], cursor_field).desc()
                )
        
        # Get one extra item to determine if there are more
        items = query.limit(limit + 1).all()
        
        has_more = len(items) > limit
        if has_more:
            items = items[:-1]
        
        # Get cursor values
        next_cursor = None
        prev_cursor = None
        
        if items:
            if direction == "next" or not cursor_value:
                next_cursor = getattr(items[-1], cursor_field) if has_more else None
                prev_cursor = getattr(items[0], cursor_field) if cursor_value else None
            else:
                # Reverse items if paginating backwards
                items.reverse()
                next_cursor = getattr(items[-1], cursor_field) if cursor_value else None
                prev_cursor = getattr(items[0], cursor_field) if has_more else None
        
        return {
            "items": items,
            "cursors": {
                "next": next_cursor,
                "prev": prev_cursor
            },
            "has_next": bool(next_cursor),
            "has_prev": bool(prev_cursor)
        }