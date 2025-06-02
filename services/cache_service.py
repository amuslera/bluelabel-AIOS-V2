"""
Cache service for ROI workflow optimization.
Provides Redis-based caching for expensive operations like transcription and translation.
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from core.config import config

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based cache service for workflow optimizations"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = not config.REDIS_SIMULATION_MODE
        
        # Cache TTL settings (in seconds)
        self.transcription_ttl = 24 * 60 * 60  # 24 hours
        self.translation_ttl = 7 * 24 * 60 * 60  # 7 days
        self.extraction_ttl = 12 * 60 * 60  # 12 hours
        
        # Cache key prefixes
        self.prefix_transcription = "roi:transcription:"
        self.prefix_translation = "roi:translation:"
        self.prefix_extraction = "roi:extraction:"
        
    async def connect(self):
        """Initialize Redis connection"""
        if not self.enabled:
            logger.info("Cache service disabled (simulation mode)")
            return
            
        try:
            self.redis_client = redis.from_url(
                config.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Cache service connected to Redis successfully")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self.enabled = False
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """Generate consistent hash for file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _generate_text_hash(self, text: str, context: str = "") -> str:
        """Generate consistent hash for text content"""
        combined = f"{text}:{context}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    async def get_transcription_cache(
        self, 
        file_content: bytes, 
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached transcription result"""
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            file_hash = self._generate_file_hash(file_content)
            context = f"lang:{language}" if language else "auto"
            cache_key = f"{self.prefix_transcription}{file_hash}:{context}"
            
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache HIT for transcription: {file_hash[:8]}...")
                return json.loads(cached_result)
            
            logger.debug(f"Cache MISS for transcription: {file_hash[:8]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving transcription cache: {e}")
            return None
    
    async def set_transcription_cache(
        self, 
        file_content: bytes, 
        result: Dict[str, Any],
        language: Optional[str] = None
    ):
        """Cache transcription result"""
        if not self.enabled or not self.redis_client:
            return
            
        try:
            file_hash = self._generate_file_hash(file_content)
            context = f"lang:{language}" if language else "auto"
            cache_key = f"{self.prefix_transcription}{file_hash}:{context}"
            
            # Store with TTL
            await self.redis_client.setex(
                cache_key, 
                self.transcription_ttl, 
                json.dumps(result)
            )
            
            logger.info(f"Cached transcription result: {file_hash[:8]}...")
            
        except Exception as e:
            logger.error(f"Error caching transcription result: {e}")
    
    async def get_translation_cache(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached translation result"""
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            text_hash = self._generate_text_hash(text, f"{source_lang}->{target_lang}")
            cache_key = f"{self.prefix_translation}{text_hash}"
            
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache HIT for translation: {text_hash[:8]}...")
                return json.loads(cached_result)
            
            logger.debug(f"Cache MISS for translation: {text_hash[:8]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving translation cache: {e}")
            return None
    
    async def set_translation_cache(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        result: Dict[str, Any]
    ):
        """Cache translation result"""
        if not self.enabled or not self.redis_client:
            return
            
        try:
            text_hash = self._generate_text_hash(text, f"{source_lang}->{target_lang}")
            cache_key = f"{self.prefix_translation}{text_hash}"
            
            # Store with TTL
            await self.redis_client.setex(
                cache_key, 
                self.translation_ttl, 
                json.dumps(result)
            )
            
            logger.info(f"Cached translation result: {text_hash[:8]}...")
            
        except Exception as e:
            logger.error(f"Error caching translation result: {e}")
    
    async def get_extraction_cache(
        self, 
        text: str, 
        language: str,
        context: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Get cached extraction result"""
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            text_hash = self._generate_text_hash(text, f"extract:{language}:{context}")
            cache_key = f"{self.prefix_extraction}{text_hash}"
            
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache HIT for extraction: {text_hash[:8]}...")
                return json.loads(cached_result)
            
            logger.debug(f"Cache MISS for extraction: {text_hash[:8]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving extraction cache: {e}")
            return None
    
    async def set_extraction_cache(
        self, 
        text: str, 
        language: str, 
        context: str, 
        result: Dict[str, Any]
    ):
        """Cache extraction result"""
        if not self.enabled or not self.redis_client:
            return
            
        try:
            text_hash = self._generate_text_hash(text, f"extract:{language}:{context}")
            cache_key = f"{self.prefix_extraction}{text_hash}"
            
            # Store with TTL
            await self.redis_client.setex(
                cache_key, 
                self.extraction_ttl, 
                json.dumps(result)
            )
            
            logger.info(f"Cached extraction result: {text_hash[:8]}...")
            
        except Exception as e:
            logger.error(f"Error caching extraction result: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
            
        try:
            # Count keys by prefix
            transcription_keys = 0
            translation_keys = 0
            extraction_keys = 0
            
            async for key in self.redis_client.scan_iter(match=f"{self.prefix_transcription}*"):
                transcription_keys += 1
            
            async for key in self.redis_client.scan_iter(match=f"{self.prefix_translation}*"):
                translation_keys += 1
                
            async for key in self.redis_client.scan_iter(match=f"{self.prefix_extraction}*"):
                extraction_keys += 1
            
            # Get Redis info
            info = await self.redis_client.info()
            
            return {
                "enabled": True,
                "transcription_cache_entries": transcription_keys,
                "translation_cache_entries": translation_keys,
                "extraction_cache_entries": extraction_keys,
                "total_keys": transcription_keys + translation_keys + extraction_keys,
                "redis_memory_used": info.get("used_memory_human", "unknown"),
                "redis_connected_clients": info.get("connected_clients", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    async def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache entries by type or all"""
        if not self.enabled or not self.redis_client:
            return
            
        try:
            if cache_type == "transcription":
                pattern = f"{self.prefix_transcription}*"
            elif cache_type == "translation":
                pattern = f"{self.prefix_translation}*"
            elif cache_type == "extraction":
                pattern = f"{self.prefix_extraction}*"
            else:
                # Clear all ROI-related cache
                patterns = [
                    f"{self.prefix_transcription}*",
                    f"{self.prefix_translation}*",
                    f"{self.prefix_extraction}*"
                ]
                
                for pattern in patterns:
                    async for key in self.redis_client.scan_iter(match=pattern):
                        await self.redis_client.delete(key)
                        
                logger.info("Cleared all ROI workflow cache")
                return
            
            # Clear specific cache type
            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
                
            logger.info(f"Cleared {cache_type} cache")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


# Global cache service instance
cache_service = CacheService()