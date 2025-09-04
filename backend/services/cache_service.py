"""
Cache Service for Baseball Trade AI
Provides unified caching interface with Redis and memory fallback
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
DEFAULT_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
MAX_MEMORY_CACHE_SIZE = 1000


class CacheService:
    """
    Unified caching service with Redis primary and memory fallback
    Provides automatic serialization and TTL management
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self._initialize_redis()
    
    def _initialize_redis(self) -> None:
        """Initialize Redis connection with error handling"""
        if not ENABLE_CACHING:
            logger.info("Caching disabled by configuration")
            return
        
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=20
            )
            logger.info("Redis cache client initialized")
        except ImportError:
            logger.warning("Redis not available, using memory-only cache")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic deserialization"""
        if not ENABLE_CACHING:
            return None
        
        try:
            # Try Redis first
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value is not None:
                    logger.debug(f"Redis cache hit: {key}")
                    return json.loads(value)
            
            # Fallback to memory cache
            if key in self.memory_cache:
                cached_item = self.memory_cache[key]
                if time.time() - cached_item['timestamp'] < cached_item['ttl']:
                    logger.debug(f"Memory cache hit: {key}")
                    return cached_item['value']
                else:
                    # Expired, remove from cache
                    del self.memory_cache[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]
            
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with automatic serialization"""
        if not ENABLE_CACHING:
            return False
        
        ttl = ttl or DEFAULT_TTL
        
        try:
            serialized_value = json.dumps(value, default=str)  # Handle datetime objects
            
            # Try Redis first
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
                logger.debug(f"Cached to Redis: {key} (TTL: {ttl}s)")
                return True
            
            # Fallback to memory cache
            current_time = time.time()
            
            # Clean up if memory cache is getting too large
            if len(self.memory_cache) >= MAX_MEMORY_CACHE_SIZE:
                await self._cleanup_memory_cache()
            
            self.memory_cache[key] = {
                'value': value,
                'timestamp': current_time,
                'ttl': ttl
            }
            self.cache_timestamps[key] = current_time
            
            logger.debug(f"Cached to memory: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            deleted = False
            
            # Delete from Redis
            if self.redis_client:
                result = await self.redis_client.delete(key)
                deleted = result > 0
            
            # Delete from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True
            
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
            
            if deleted:
                logger.debug(f"Deleted from cache: {key}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_client:
                return await self.redis_client.exists(key) > 0
            
            return (key in self.memory_cache and 
                    time.time() - self.memory_cache[key]['timestamp'] < self.memory_cache[key]['ttl'])
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern (Redis only)"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for '{pattern}': {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'enabled': ENABLE_CACHING,
            'redis_available': self.redis_client is not None,
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max_size': MAX_MEMORY_CACHE_SIZE
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats['redis_info'] = {
                    'used_memory': info.get('used_memory_human', 'unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats
    
    async def _cleanup_memory_cache(self) -> None:
        """Clean expired entries from memory cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, cached_item in self.memory_cache.items():
            if current_time - cached_item['timestamp'] >= cached_item['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
        
        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
        
        # If still too large, remove oldest entries
        if len(self.memory_cache) >= MAX_MEMORY_CACHE_SIZE:
            sorted_keys = sorted(
                self.cache_timestamps.items(),
                key=lambda x: x[1]
            )
            keys_to_remove = sorted_keys[:len(sorted_keys) // 4]  # Remove oldest 25%
            
            for key, _ in keys_to_remove:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
            
            logger.info(f"Evicted {len(keys_to_remove)} oldest cache entries")
    
    # Specific cache methods for common use cases
    
    async def get_analysis_response(self, analysis_id: str):
        """Get cached analysis response"""
        return await self.get(f"analysis_response:{analysis_id}")
    
    async def set_analysis_response(self, analysis_id: str, response, ttl: Optional[int] = None):
        """Cache analysis response"""
        return await self.set(f"analysis_response:{analysis_id}", response, ttl)
    
    async def delete_analysis_response(self, analysis_id: str):
        """Delete cached analysis response"""
        return await self.delete(f"analysis_response:{analysis_id}")
    
    async def get_team_roster(self, team_key: str):
        """Get cached team roster"""
        return await self.get(f"roster:{team_key}")
    
    async def set_team_roster(self, team_key: str, roster_data, ttl: Optional[int] = None):
        """Cache team roster"""
        return await self.set(f"roster:{team_key}", roster_data, ttl)
    
    async def get_team_stats(self, team_key: str):
        """Get cached team statistics"""
        return await self.get(f"stats:{team_key}")
    
    async def set_team_stats(self, team_key: str, stats_data, ttl: Optional[int] = None):
        """Cache team statistics"""
        return await self.set(f"stats:{team_key}", stats_data, ttl)
    
    async def invalidate_team_cache(self, team_key: str):
        """Invalidate all cache entries for a team"""
        patterns = [
            f"roster:{team_key}*",
            f"stats:{team_key}*",
            f"needs:{team_key}*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            cleared = await self.clear_pattern(pattern)
            total_cleared += cleared
        
        logger.info(f"Invalidated {total_cleared} cache entries for team {team_key}")
        return total_cleared
    
    async def warm_cache(self) -> Dict[str, int]:
        """Warm cache with frequently accessed data"""
        if not ENABLE_CACHING:
            return {'message': 'Caching disabled'}
        
        warmed_counts = {
            'teams': 0,
            'rosters': 0,
            'stats': 0
        }
        
        try:
            # This would be implemented to pre-load common data
            # For now, return empty counts
            logger.info("Cache warming completed")
            return warmed_counts
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return {'error': str(e)}


# Global cache service instance
cache_service = CacheService()