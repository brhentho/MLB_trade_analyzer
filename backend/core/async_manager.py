"""
Async/Sync Management System
Handles proper async patterns, prevents asyncio.run() in async contexts,
and provides utilities for async resource management
"""

import asyncio
import logging
import functools
import inspect
from typing import Any, Callable, Dict, Optional, TypeVar, Union, Awaitable
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncContextError(Exception):
    """Raised when trying to run sync operations in async context improperly"""
    pass


class AsyncManager:
    """
    Central manager for async operations and context handling
    """
    
    def __init__(self):
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._running_loops: Dict[int, asyncio.AbstractEventLoop] = {}
        self._context_managers: weakref.WeakSet = weakref.WeakSet()
    
    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        """Get or create thread pool for sync operations"""
        if self._thread_pool is None or self._thread_pool._shutdown:
            self._thread_pool = ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix="baseball-sync-"
            )
        return self._thread_pool
    
    def is_running_in_async_context(self) -> bool:
        """Check if we're currently running in an async context"""
        try:
            asyncio.current_task()
            return True
        except RuntimeError:
            return False
    
    def get_current_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Safely get the current event loop"""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return None
    
    async def run_in_thread(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Run a synchronous function in a thread pool
        
        Args:
            func: Synchronous function to run
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function execution
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            functools.partial(func, *args, **kwargs)
        )
    
    def run_async_safe(self, coro: Awaitable[T]) -> T:
        """
        Safely run an async coroutine, handling both sync and async contexts
        
        Args:
            coro: Coroutine to run
            
        Returns:
            Result of the coroutine
            
        Raises:
            AsyncContextError: If called improperly in async context
        """
        if self.is_running_in_async_context():
            raise AsyncContextError(
                "Cannot use run_async_safe() from within an async context. "
                "Use 'await' instead."
            )
        
        try:
            # Try to get existing loop
            loop = asyncio.get_running_loop()
            raise AsyncContextError(
                "Event loop is running but no async context detected. "
                "This should not happen."
            )
        except RuntimeError:
            # No loop running, safe to create new one
            return asyncio.run(coro)
    
    async def safe_gather(self, *coros, return_exceptions: bool = True) -> list:
        """
        Safely gather coroutines with proper error handling
        
        Args:
            *coros: Coroutines to run concurrently
            return_exceptions: Whether to return exceptions instead of raising
            
        Returns:
            List of results or exceptions
        """
        try:
            return await asyncio.gather(*coros, return_exceptions=return_exceptions)
        except Exception as e:
            logger.error(f"Error in safe_gather: {e}")
            if return_exceptions:
                return [e for _ in coros]
            raise
    
    async def with_timeout(self, coro: Awaitable[T], timeout: float) -> T:
        """
        Run a coroutine with a timeout
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds
            
        Returns:
            Result of the coroutine
            
        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            raise
    
    @asynccontextmanager
    async def async_resource(self, resource_factory: Callable[[], Awaitable[T]], 
                           cleanup_factory: Optional[Callable[[T], Awaitable[None]]] = None):
        """
        Async context manager for resource management
        
        Args:
            resource_factory: Function that creates the resource
            cleanup_factory: Optional function to cleanup the resource
        """
        resource = None
        try:
            resource = await resource_factory()
            yield resource
        finally:
            if resource is not None and cleanup_factory is not None:
                try:
                    await cleanup_factory(resource)
                except Exception as e:
                    logger.error(f"Error cleaning up resource: {e}")
    
    async def shutdown(self):
        """Shutdown the async manager and cleanup resources"""
        if self._thread_pool and not self._thread_pool._shutdown:
            self._thread_pool.shutdown(wait=True)
        
        # Cleanup any remaining context managers
        for cm in list(self._context_managers):
            try:
                if hasattr(cm, '__aexit__'):
                    await cm.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error cleaning up context manager: {e}")


def async_to_sync(func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    """
    Decorator to convert an async function to sync
    WARNING: Only use this for functions that MUST be sync (like __init__)
    
    Args:
        func: Async function to convert
        
    Returns:
        Sync wrapper function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return async_manager.run_async_safe(func(*args, **kwargs))
    return wrapper


def sync_to_async(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to run a sync function in a thread pool
    
    Args:
        func: Sync function to convert
        
    Returns:
        Async wrapper function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await async_manager.run_in_thread(func, *args, **kwargs)
    return wrapper


def ensure_async(func_or_coro: Union[Callable, Awaitable]) -> Awaitable:
    """
    Ensure a function or coroutine is awaitable
    
    Args:
        func_or_coro: Function or coroutine
        
    Returns:
        Awaitable version
    """
    if inspect.iscoroutinefunction(func_or_coro):
        return func_or_coro()
    elif inspect.iscoroutine(func_or_coro):
        return func_or_coro
    elif callable(func_or_coro):
        # Wrap sync function
        async def async_wrapper():
            return await async_manager.run_in_thread(func_or_coro)
        return async_wrapper()
    else:
        # Already a value, wrap in coroutine
        async def value_wrapper():
            return func_or_coro
        return value_wrapper()


class AsyncServiceMixin:
    """
    Mixin for services that need proper async/sync handling
    """
    
    def __init__(self):
        self._async_manager = async_manager
        self._initialization_lock = asyncio.Lock()
        self._is_initialized = False
    
    async def async_init(self):
        """Override this method for async initialization"""
        pass
    
    async def ensure_initialized(self):
        """Ensure the service is initialized"""
        if not self._is_initialized:
            async with self._initialization_lock:
                if not self._is_initialized:
                    await self.async_init()
                    self._is_initialized = True
    
    async def async_cleanup(self):
        """Override this method for async cleanup"""
        pass


class DatabaseConnectionManager:
    """
    Async database connection manager with proper resource handling
    """
    
    def __init__(self):
        self._connections: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
    
    async def get_connection(self, connection_id: str = "default"):
        """Get or create a database connection"""
        if connection_id not in self._locks:
            self._locks[connection_id] = asyncio.Lock()
        
        async with self._locks[connection_id]:
            if connection_id not in self._connections:
                # Create new connection (implement based on your DB)
                self._connections[connection_id] = await self._create_connection()
        
        return self._connections[connection_id]
    
    async def _create_connection(self):
        """Override this to create actual database connections"""
        # Placeholder - implement with your actual database client
        pass
    
    async def close_all_connections(self):
        """Close all database connections"""
        for conn_id, connection in self._connections.items():
            try:
                if hasattr(connection, 'close'):
                    if inspect.iscoroutinefunction(connection.close):
                        await connection.close()
                    else:
                        connection.close()
            except Exception as e:
                logger.error(f"Error closing connection {conn_id}: {e}")
        
        self._connections.clear()


# Global instances
async_manager = AsyncManager()
db_connection_manager = DatabaseConnectionManager()


# Utility functions
async def safe_async_call(func_or_coro: Union[Callable, Awaitable], 
                         *args, 
                         timeout: Optional[float] = None,
                         **kwargs) -> Any:
    """
    Safely call an async function or coroutine with timeout and error handling
    
    Args:
        func_or_coro: Function or coroutine to call
        *args: Arguments
        timeout: Optional timeout in seconds
        **kwargs: Keyword arguments
        
    Returns:
        Result of the call or None if failed
    """
    try:
        if inspect.iscoroutinefunction(func_or_coro):
            coro = func_or_coro(*args, **kwargs)
        elif inspect.iscoroutine(func_or_coro):
            coro = func_or_coro
        else:
            # Sync function, run in thread
            return await async_manager.run_in_thread(func_or_coro, *args, **kwargs)
        
        if timeout:
            return await async_manager.with_timeout(coro, timeout)
        else:
            return await coro
            
    except Exception as e:
        logger.error(f"Error in safe_async_call: {e}")
        return None


@asynccontextmanager
async def async_nullcontext():
    """
    Async version of contextlib.nullcontext()
    For compatibility when PerformanceTracker might be None
    """
    yield None


def create_async_context_manager(enter_func: Callable, exit_func: Optional[Callable] = None):
    """
    Create an async context manager from functions
    
    Args:
        enter_func: Function to call on enter
        exit_func: Optional function to call on exit
        
    Returns:
        Async context manager
    """
    @asynccontextmanager
    async def context_manager():
        resource = None
        try:
            if inspect.iscoroutinefunction(enter_func):
                resource = await enter_func()
            else:
                resource = await async_manager.run_in_thread(enter_func)
            yield resource
        finally:
            if exit_func and resource is not None:
                try:
                    if inspect.iscoroutinefunction(exit_func):
                        await exit_func(resource)
                    else:
                        await async_manager.run_in_thread(exit_func, resource)
                except Exception as e:
                    logger.error(f"Error in exit function: {e}")
    
    return context_manager()