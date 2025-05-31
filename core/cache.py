"""
Redis caching layer for performance optimization.
"""
import json
import pickle
import hashlib
from typing import Any, Optional, Union, Callable
from functools import wraps
from datetime import timedelta
import logging
import redis
from redis.exceptions import RedisError

from core.config import config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage Redis caching with multiple serialization strategies"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or config.cache.redis_url
        self._client = None
        self._connected = False
        
    @property
    def client(self) -> redis.Redis:
        """Get Redis client with lazy connection"""
        if not self._client:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # Handle binary data
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                self._client.ping()
                self._connected = True
                logger.info("Redis connection established")
            except RedisError as e:
                logger.error(f"Redis connection failed: {e}")
                self._connected = False
                raise
        return self._client
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_hash = hashlib.md5(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if not self._connected:
            return default
            
        try:
            value = self.client.get(key)
            if value is None:
                return default
                
            # Try JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
                
        except RedisError as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self._connected:
            return False
            
        try:
            # Try JSON first for better interoperability
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
            
            if ttl:
                return bool(self.client.setex(key, ttl, serialized))
            else:
                return bool(self.client.set(key, serialized))
                
        except RedisError as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._connected:
            return False
            
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._connected:
            return False
            
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self._connected:
            return 0
            
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self._connected:
            return {"connected": False}
            
        try:
            info = self.client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except RedisError as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


# Global cache instance
cache_manager = CacheManager()


def cache(
    ttl: Union[int, timedelta] = 300,
    prefix: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds or timedelta
        prefix: Cache key prefix (defaults to function name)
        key_func: Custom key generation function
    """
    def decorator(func):
        cache_prefix = prefix or f"func:{func.__module__}.{func.__name__}"
        cache_ttl = ttl.total_seconds() if isinstance(ttl, timedelta) else ttl
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{cache_prefix}:{key_func(*args, **kwargs)}"
            else:
                cache_key = cache_manager._generate_key(cache_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                cache_manager.client.hincrby("cache_metrics", "hits", 1)
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            cache_manager.client.hincrby("cache_metrics", "misses", 1)
            
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, int(cache_ttl))
            
            return result
        
        # Add cache control methods
        wrapper.invalidate = lambda *args, **kwargs: cache_manager.delete(
            cache_manager._generate_key(cache_prefix, *args, **kwargs)
        )
        wrapper.invalidate_all = lambda: cache_manager.clear_pattern(f"{cache_prefix}:*")
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    cleared = cache_manager.clear_pattern(pattern)
    logger.info(f"Invalidated {cleared} cache entries matching {pattern}")
    return cleared


# Cache warmup functions
async def warm_cache():
    """Warm up cache with frequently accessed data"""
    from apps.api.routers.marketplace import get_featured_agents, get_agent_categories
    from apps.api.dependencies.database import get_db
    
    logger.info("Starting cache warmup...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Warm up featured agents
        featured = await get_featured_agents(db)
        cache_manager.set("featured_agents", featured, ttl=3600)
        
        # Warm up categories
        categories = await get_agent_categories(db)
        cache_manager.set("agent_categories", categories, ttl=3600)
        
        logger.info("Cache warmup completed")
        
    except Exception as e:
        logger.error(f"Cache warmup failed: {e}")
    finally:
        db.close()


# Cache invalidation strategies
class CacheInvalidator:
    """Handle cache invalidation strategies"""
    
    @staticmethod
    def invalidate_user_cache(user_id: str):
        """Invalidate all user-related cache"""
        patterns = [
            f"user:{user_id}:*",
            f"user_installations:{user_id}",
            f"user_reviews:{user_id}"
        ]
        for pattern in patterns:
            invalidate_cache(pattern)
    
    @staticmethod
    def invalidate_agent_cache(agent_id: str):
        """Invalidate all agent-related cache"""
        patterns = [
            f"agent:{agent_id}:*",
            f"agent_stats:{agent_id}",
            f"agent_reviews:{agent_id}",
            "featured_agents",  # Featured agents might have changed
            "popular_agents"
        ]
        for pattern in patterns:
            invalidate_cache(pattern)
    
    @staticmethod
    def invalidate_marketplace_cache():
        """Invalidate marketplace-wide cache"""
        patterns = [
            "featured_agents",
            "agent_categories",
            "popular_agents",
            "marketplace_stats"
        ]
        for pattern in patterns:
            invalidate_cache(pattern)