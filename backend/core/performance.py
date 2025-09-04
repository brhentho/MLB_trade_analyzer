"""
Advanced Performance Optimization and Resource Management
Handles caching, connection pooling, memory optimization, and performance monitoring
"""

import asyncio
import gc
import psutil
import time
import threading
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import asynccontextmanager, contextmanager
from functools import wraps, lru_cache
import weakref
import os
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_delta: Optional[float] = None
    cpu_percent: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryOptimizer:
    """
    Memory optimization utilities for better garbage collection
    and memory usage tracking
    """
    
    def __init__(self):
        self.gc_thresholds = gc.get_threshold()
        self.memory_alerts = deque(maxlen=100)
        self.memory_threshold = 85  # Alert when memory usage > 85%
        self._last_gc_time = time.time()
        self._gc_interval = 30  # Seconds between forced GC
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # System memory info
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory_mb': memory_info.rss / 1024 / 1024,
            'process_memory_percent': memory_percent,
            'system_memory_percent': system_memory.percent,
            'system_available_mb': system_memory.available / 1024 / 1024,
            'gc_stats': {
                'generation_0': gc.get_count()[0],
                'generation_1': gc.get_count()[1],
                'generation_2': gc.get_count()[2],
                'total_collections': sum(gc.get_stats()[i]['collections'] for i in range(3))
            }
        }
    
    def optimize_gc(self):
        """Optimize garbage collection settings"""
        # More aggressive GC for memory-intensive operations
        gc.set_threshold(700, 10, 10)  # More frequent collections
        
        current_time = time.time()
        if current_time - self._last_gc_time > self._gc_interval:
            collected = gc.collect()
            self._last_gc_time = current_time
            logger.debug(f"Manual garbage collection collected {collected} objects")
    
    def check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure"""
        memory_info = self.get_memory_info()
        
        if memory_info['system_memory_percent'] > self.memory_threshold:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'system_memory_percent': memory_info['system_memory_percent'],
                'process_memory_mb': memory_info['process_memory_mb']
            }
            self.memory_alerts.append(alert)
            logger.warning(f"High memory usage detected: {memory_info['system_memory_percent']:.1f}%")
            return True
        
        return False
    
    def cleanup_memory(self):
        """Force memory cleanup"""
        # Clear caches
        gc.collect()
        
        # Clear function caches
        for obj in gc.get_objects():
            if hasattr(obj, 'cache_clear'):
                try:
                    obj.cache_clear()
                except:
                    pass
        
        logger.info("Memory cleanup completed")


class ConnectionPool:
    """
    Generic connection pool for database and external service connections
    """
    
    def __init__(self, connection_factory: Callable, max_size: int = 10, min_size: int = 2):
        self.connection_factory = connection_factory
        self.max_size = max_size
        self.min_size = min_size
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._connections: weakref.WeakSet = weakref.WeakSet()
        self._lock = asyncio.Lock()
        self._created_count = 0
        self._closed = False
    
    async def initialize(self):
        """Initialize the connection pool"""
        async with self._lock:
            for _ in range(self.min_size):
                conn = await self._create_connection()
                await self._pool.put(conn)
    
    async def _create_connection(self):
        """Create a new connection"""
        if self._created_count >= self.max_size:
            raise RuntimeError("Connection pool exhausted")
        
        conn = await self.connection_factory()
        self._connections.add(conn)
        self._created_count += 1
        logger.debug(f"Created new connection (total: {self._created_count})")
        return conn
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        conn = None
        try:
            # Try to get an existing connection
            try:
                conn = await asyncio.wait_for(self._pool.get(), timeout=5.0)
            except asyncio.TimeoutError:
                # Create new connection if pool is empty and under limit
                async with self._lock:
                    if self._created_count < self.max_size:
                        conn = await self._create_connection()
                    else:
                        # Wait longer for a connection
                        conn = await self._pool.get()
            
            yield conn
            
        finally:
            if conn and not self._closed:
                # Return connection to pool
                try:
                    await self._pool.put(conn)
                except asyncio.QueueFull:
                    # Pool is full, close the connection
                    if hasattr(conn, 'close'):
                        await conn.close()
                    self._created_count -= 1
    
    async def close(self):
        """Close all connections in the pool"""
        self._closed = True
        
        # Close all connections in the queue
        while not self._pool.empty():
            try:
                conn = await asyncio.wait_for(self._pool.get(), timeout=1.0)
                if hasattr(conn, 'close'):
                    await conn.close()
            except asyncio.TimeoutError:
                break
        
        # Close any remaining connections
        for conn in list(self._connections):
            try:
                if hasattr(conn, 'close'):
                    await conn.close()
            except:
                pass
        
        logger.info(f"Closed connection pool with {self._created_count} connections")


class AdvancedCache:
    """
    Advanced caching system with TTL, LRU eviction, and memory management
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Check TTL
            if time.time() - self._timestamps[key] > self.default_ttl:
                await self._evict(key)
                self._misses += 1
                return None
            
            # Update access time for LRU
            self._access_times[key] = time.time()
            self._hits += 1
            
            return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        async with self._lock:
            # Check if we need to make space
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._access_times[key] = time.time()
    
    async def delete(self, key: str):
        """Delete key from cache"""
        async with self._lock:
            await self._evict(key)
    
    async def _evict(self, key: str):
        """Evict a specific key"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_times.pop(key, None)
        self._evictions += 1
    
    async def _evict_lru(self):
        """Evict least recently used item"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        await self._evict(lru_key)
        logger.debug(f"Evicted LRU key: {lru_key}")
    
    async def cleanup_expired(self):
        """Clean up expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.default_ttl
        ]
        
        for key in expired_keys:
            await self._evict(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_rate': hit_rate,
            'hits': self._hits,
            'misses': self._misses,
            'evictions': self._evictions
        }


class PerformanceProfiler:
    """
    Advanced performance profiler with detailed metrics collection
    """
    
    def __init__(self):
        self.metrics: deque = deque(maxlen=10000)
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_operations: deque = deque(maxlen=100)
        self.memory_optimizer = MemoryOptimizer()
        self._lock = threading.Lock()
    
    @contextmanager
    def profile_operation(self, operation_name: str, metadata: Optional[Dict] = None):
        """Context manager for profiling operations"""
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        # Get initial memory
        memory_info = self.memory_optimizer.get_memory_info()
        metric.memory_before = memory_info['process_memory_mb']
        
        try:
            yield metric
            metric.success = True
            
        except Exception as e:
            metric.success = False
            metric.error = str(e)
            raise
            
        finally:
            metric.end_time = time.time()
            metric.duration = metric.end_time - metric.start_time
            
            # Get final memory
            memory_info = self.memory_optimizer.get_memory_info()
            metric.memory_after = memory_info['process_memory_mb']
            metric.memory_delta = metric.memory_after - metric.memory_before
            metric.cpu_percent = psutil.cpu_percent()
            
            self._record_metric(metric)
    
    def _record_metric(self, metric: PerformanceMetrics):
        """Record performance metric"""
        with self._lock:
            self.metrics.append(metric)
            
            if metric.success and metric.duration:
                self.operation_stats[metric.operation_name].append(metric.duration)
                
                # Keep only recent measurements
                if len(self.operation_stats[metric.operation_name]) > 1000:
                    self.operation_stats[metric.operation_name] = \
                        self.operation_stats[metric.operation_name][-1000:]
                
                # Track slow operations
                if metric.duration > 1.0:  # Operations > 1 second
                    self.slow_operations.append({
                        'operation': metric.operation_name,
                        'duration': metric.duration,
                        'timestamp': metric.start_time,
                        'metadata': metric.metadata
                    })
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        with self._lock:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_operations': len(self.metrics),
                'memory_info': self.memory_optimizer.get_memory_info(),
                'operation_stats': {},
                'slow_operations': list(self.slow_operations)[-10:],  # Last 10 slow ops
                'memory_alerts': list(self.memory_optimizer.memory_alerts)[-5:]  # Last 5 alerts
            }
            
            # Calculate statistics for each operation
            for op_name, durations in self.operation_stats.items():
                if durations:
                    report['operation_stats'][op_name] = {
                        'count': len(durations),
                        'avg_duration': sum(durations) / len(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations)
                    }
            
            return report
    
    def optimize_performance(self):
        """Perform performance optimizations"""
        # Memory optimization
        if self.memory_optimizer.check_memory_pressure():
            self.memory_optimizer.cleanup_memory()
        
        # GC optimization
        self.memory_optimizer.optimize_gc()
        
        logger.info("Performance optimization completed")


class ResourceManager:
    """
    Centralized resource management for connections, caches, and system resources
    """
    
    def __init__(self):
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.caches: Dict[str, AdvancedCache] = {}
        self.profiler = PerformanceProfiler()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
    
    def add_connection_pool(self, name: str, pool: ConnectionPool):
        """Add a connection pool"""
        self.connection_pools[name] = pool
    
    def add_cache(self, name: str, cache: AdvancedCache):
        """Add a cache"""
        self.caches[name] = cache
    
    def get_connection_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get connection pool by name"""
        return self.connection_pools.get(name)
    
    def get_cache(self, name: str) -> Optional[AdvancedCache]:
        """Get cache by name"""
        return self.caches.get(name)
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self._monitor_task = asyncio.create_task(self._performance_monitor())
        logger.info("Started resource monitoring")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while True:
            try:
                # Clean up caches
                for cache in self.caches.values():
                    await cache.cleanup_expired()
                
                # Optimize performance
                self.profiler.optimize_performance()
                
                await asyncio.sleep(60)  # Run every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _performance_monitor(self):
        """Performance monitoring task"""
        while True:
            try:
                report = self.profiler.get_performance_report()
                
                # Log performance issues
                if report['memory_info']['system_memory_percent'] > 85:
                    logger.warning(f"High memory usage: {report['memory_info']['system_memory_percent']:.1f}%")
                
                if report['slow_operations']:
                    logger.warning(f"Slow operations detected: {len(report['slow_operations'])}")
                
                await asyncio.sleep(300)  # Monitor every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(300)
    
    async def shutdown(self):
        """Shutdown all resources"""
        # Cancel monitoring tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()
        
        # Close connection pools
        for pool in self.connection_pools.values():
            await pool.close()
        
        logger.info("Resource manager shutdown completed")


# Performance decorators
def profile_performance(operation_name: Optional[str] = None):
    """Decorator to profile function performance"""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with resource_manager.profiler.profile_operation(op_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with resource_manager.profiler.profile_operation(op_name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


def cache_result(cache_name: str = "default", ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = resource_manager.get_cache(cache_name)
            if not cache:
                return await func(*args, **kwargs)
            
            # Generate cache key
            import hashlib
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try cache first
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global resource manager
resource_manager = ResourceManager()


# Utility functions
async def setup_default_resources():
    """Setup default caches and monitoring"""
    # Add default cache
    default_cache = AdvancedCache(max_size=1000, default_ttl=300)
    resource_manager.add_cache("default", default_cache)
    
    # Start monitoring
    await resource_manager.start_monitoring()
    
    logger.info("Default resources initialized")


async def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics"""
    return {
        'performance': resource_manager.profiler.get_performance_report(),
        'cache_stats': {
            name: cache.get_stats() 
            for name, cache in resource_manager.caches.items()
        },
        'connection_pools': {
            name: {
                'created_connections': pool._created_count,
                'max_size': pool.max_size,
                'closed': pool._closed
            }
            for name, pool in resource_manager.connection_pools.items()
        }
    }