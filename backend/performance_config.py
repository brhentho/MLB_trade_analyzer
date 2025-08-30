"""
Performance Configuration and Optimization Module
Handles caching, connection pooling, and performance monitoring
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
import asyncio

logger = logging.getLogger(__name__)

# Redis configuration (with fallbacks)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes default

# Database connection pooling
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_POOL_MAX_OVERFLOW = int(os.getenv('DB_POOL_MAX_OVERFLOW', '5'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

# Performance monitoring
ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
SLOW_QUERY_THRESHOLD = float(os.getenv('SLOW_QUERY_THRESHOLD', '1.0'))  # 1 second

class PerformanceCache:
    """Simple in-memory cache with TTL fallback when Redis unavailable"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.initialize_redis()
    
    def initialize_redis(self):
        """Initialize Redis connection if available"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            logger.info("Redis cache initialized successfully")
        except ImportError:
            logger.warning("Redis not available, using in-memory cache")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not ENABLE_CACHING:
            return None
        
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    import json
                    return json.loads(value)
            else:
                # Fallback to memory cache
                if key in self.memory_cache:
                    import time
                    if time.time() - self.cache_timestamps[key] < CACHE_TTL:
                        return self.memory_cache[key]
                    else:
                        # Expired
                        del self.memory_cache[key]
                        del self.cache_timestamps[key]
            
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not ENABLE_CACHING:
            return False
        
        ttl = ttl or CACHE_TTL
        
        try:
            if self.redis_client:
                import json
                await self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            else:
                # Fallback to memory cache
                import time
                self.memory_cache[key] = value
                self.cache_timestamps[key] = time.time()
                
                # Clean expired entries periodically
                if len(self.memory_cache) > 1000:  # Limit memory usage
                    await self._cleanup_memory_cache()
                
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            
            if key in self.memory_cache:
                del self.memory_cache[key]
                del self.cache_timestamps[key]
            
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def _cleanup_memory_cache(self):
        """Clean expired entries from memory cache"""
        import time
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp > CACHE_TTL
        ]
        
        for key in expired_keys:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
        
        logger.info(f"Cleaned {len(expired_keys)} expired cache entries")

# Global cache instance
cache = PerformanceCache()

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.request_times = {}
        self.slow_queries = []
        self.error_counts = {}
    
    async def track_request(self, endpoint: str, duration: float):
        """Track request performance"""
        if not ENABLE_PERFORMANCE_MONITORING:
            return
        
        if endpoint not in self.request_times:
            self.request_times[endpoint] = []
        
        self.request_times[endpoint].append(duration)
        
        # Keep only recent measurements (last 1000)
        if len(self.request_times[endpoint]) > 1000:
            self.request_times[endpoint] = self.request_times[endpoint][-1000:]
        
        # Log slow requests
        if duration > SLOW_QUERY_THRESHOLD:
            slow_query_info = {
                'endpoint': endpoint,
                'duration': duration,
                'timestamp': logger.time()
            }
            self.slow_queries.append(slow_query_info)
            logger.warning(f"Slow request detected: {endpoint} took {duration:.2f}s")
    
    async def track_error(self, error_type: str):
        """Track error occurrences"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {
            'cache_stats': {
                'enabled': ENABLE_CACHING,
                'memory_cache_size': len(cache.memory_cache),
                'redis_available': cache.redis_client is not None
            },
            'request_stats': {},
            'error_stats': self.error_counts,
            'slow_queries_count': len(self.slow_queries)
        }
        
        # Calculate average response times
        for endpoint, times in self.request_times.items():
            if times:
                stats['request_stats'][endpoint] = {
                    'avg_response_time': sum(times) / len(times),
                    'min_response_time': min(times),
                    'max_response_time': max(times),
                    'request_count': len(times)
                }
        
        return stats

# Global performance monitor
monitor = PerformanceMonitor()

# Cache key generators
def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate consistent cache key"""
    import hashlib
    key_parts = [prefix] + [str(arg) for arg in args]
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

# Caching decorators
def cached_response(cache_key_prefix: str, ttl: Optional[int] = None):
    """Decorator for caching API responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(cache_key_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator

# Database query optimization helpers
class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_team_query() -> str:
        """Optimized query for team data with proper indexing hints"""
        return """
        SELECT 
            id, team_key, name, abbreviation, city, division, league,
            budget_level, competitive_window, market_size, philosophy,
            primary_color, secondary_color
        FROM teams 
        WHERE active = true 
        ORDER BY league, division, name
        """
    
    @staticmethod
    def optimize_roster_query(team_id: int) -> str:
        """Optimized query for roster data"""
        return """
        SELECT 
            p.player_name, p.position, p.jersey_number, p.status,
            c.salary, c.years_remaining, c.option_years,
            s.games_played, s.batting_avg, s.era, s.war
        FROM players p
        LEFT JOIN contracts c ON p.id = c.player_id
        LEFT JOIN stats_cache s ON p.id = s.player_id AND s.season = 2024
        WHERE p.team_id = $1 AND p.active = true
        ORDER BY p.position, p.jersey_number
        """
    
    @staticmethod
    def optimize_analysis_query(analysis_id: str) -> str:
        """Optimized query for trade analysis data"""
        return """
        SELECT 
            analysis_id, requesting_team_id, request_text, urgency, status,
            created_at, updated_at, progress, results, error_message, cost_info
        FROM trade_analysis 
        WHERE analysis_id = $1
        """

# Connection pooling configuration
async def setup_database_pool():
    """Setup database connection pool for better performance"""
    try:
        import asyncpg
        from urllib.parse import urlparse
        
        database_url = os.getenv('SUPABASE_URL', '')
        if not database_url:
            logger.warning("No database URL configured, skipping pool setup")
            return None
        
        # Parse URL for asyncpg
        parsed = urlparse(database_url)
        pool = await asyncpg.create_pool(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else None,
            min_size=2,
            max_size=DB_POOL_SIZE,
            max_inactive_connection_lifetime=300,
            command_timeout=30
        )
        
        logger.info(f"Database pool created with {DB_POOL_SIZE} connections")
        return pool
        
    except ImportError:
        logger.warning("asyncpg not available, using default connection handling")
        return None
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        return None

# Async context manager for performance tracking
class PerformanceTracker:
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    async def __aenter__(self):
        import time
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            await monitor.track_request(self.operation_name, duration)
        
        if exc_type:
            await monitor.track_error(str(exc_type))