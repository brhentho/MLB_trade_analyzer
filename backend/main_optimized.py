"""
Baseball Trade AI - Optimized Production Application
Consolidated architecture with performance optimizations and scalability improvements
"""

import asyncio
import logging
import os
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import optimized API routers
from api.v1.routers import trades, teams, players, health

# Import services
from services.supabase_service import supabase_service
from services.cache_service import cache_service
from services.queue_service import queue_service
from performance_config import monitor, PerformanceTracker

# Import exceptions
from api.exceptions import TradeAIException, DatabaseException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application configuration
APP_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Security configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://localhost:3000').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Global state for graceful shutdown
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    
    # Startup
    logger.info("Starting Baseball Trade AI - Optimized Version")
    
    # Initialize services
    await initialize_services()
    
    # Setup signal handlers for graceful shutdown
    setup_shutdown_handlers()
    
    # Start background services
    await start_background_services()
    
    logger.info(f"Application started successfully on version {APP_VERSION}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Baseball Trade AI...")
    await shutdown_services()
    logger.info("Shutdown complete")


async def initialize_services():
    """Initialize all application services"""
    
    # Check database connectivity
    health = await supabase_service.health_check()
    if health['status'] != 'healthy':
        logger.warning(f"Database health check failed: {health}")
    else:
        logger.info(f"Database connected - {health['teams_count']} teams available")
    
    # Initialize cache service
    cache_stats = await cache_service.get_stats()
    logger.info(f"Cache service initialized - Redis: {cache_stats['redis_available']}")
    
    # Warm cache with essential data
    try:
        await cache_service.warm_cache()
        logger.info("Cache warming completed")
    except Exception as e:
        logger.warning(f"Cache warming failed: {e}")


async def start_background_services():
    """Start background services and workers"""
    
    # Queue service worker is started automatically when tasks are enqueued
    queue_stats = await queue_service.get_queue_stats()
    logger.info(f"Queue service ready - {queue_stats['total_tasks']} total tasks")
    
    # Schedule periodic tasks
    asyncio.create_task(periodic_cleanup())


async def shutdown_services():
    """Gracefully shutdown all services"""
    
    # Signal shutdown to all services
    shutdown_event.set()
    
    # Shutdown queue service
    await queue_service.shutdown()
    
    # Clear caches
    if hasattr(cache_service, 'redis_client') and cache_service.redis_client:
        try:
            await cache_service.redis_client.close()
        except:
            pass
    
    logger.info("All services shut down gracefully")


def setup_shutdown_handlers():
    """Setup signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(shutdown_services())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


async def periodic_cleanup():
    """Periodic maintenance tasks"""
    
    while not shutdown_event.is_set():
        try:
            # Schedule cleanup task every hour
            await queue_service.enqueue_task(
                task_type='cleanup',
                payload={'type': 'periodic_maintenance'},
                priority=queue_service.TaskPriority.LOW
            )
            
            # Wait 1 hour or until shutdown
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=3600)
                break  # Shutdown requested
            except asyncio.TimeoutError:
                continue  # Continue periodic tasks
                
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry


# Create FastAPI application
app = FastAPI(
    title="Baseball Trade AI - Optimized",
    description="Production-ready MLB trade analysis API with AI agents and live data",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if os.getenv('ENVIRONMENT') != 'production' else None,
    redoc_url="/redoc" if os.getenv('ENVIRONMENT') != 'production' else None
)

# Add security middlewares
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS + ['*'] if os.getenv('ENVIRONMENT') == 'development' else ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["x-rate-limit-remaining", "x-rate-limit-reset"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Add performance monitoring and security headers"""
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    
    # Track performance if monitor is available
    if monitor:
        endpoint = f"{request.method} {request.url.path}"
        await monitor.track_request(endpoint, process_time)
    
    # Add security headers
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Process-Time": str(round(process_time * 1000, 2)),
        "X-API-Version": APP_VERSION
    })
    
    # Add cache control headers
    if request.url.path.startswith("/api/v1/teams") or request.url.path.startswith("/api/v1/players"):
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response


# Exception handlers
@app.exception_handler(TradeAIException)
async def trade_ai_exception_handler(request: Request, exc: TradeAIException):
    """Handle custom Trade AI exceptions"""
    logger.error(f"Trade AI Exception: {exc.message}")
    
    if monitor:
        await monitor.track_error(exc.__class__.__name__)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc}")
    
    if monitor:
        await monitor.track_error("ValidationError")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    
    if monitor:
        await monitor.track_error(f"HTTP_{exc.status_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    if monitor:
        await monitor.track_error("UnhandledException")
    
    # Don't expose internal errors in production
    if os.getenv('ENVIRONMENT') == 'production':
        message = "An internal error occurred"
        details = None
    else:
        message = str(exc)
        details = {"exception_type": exc.__class__.__name__}
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


# Include API routers
app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(trades.router, prefix=API_PREFIX, tags=["Trades"]) 
app.include_router(teams.router, prefix=API_PREFIX, tags=["Teams"])
app.include_router(players.router, prefix=API_PREFIX, tags=["Players"])


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with system overview"""
    
    async with PerformanceTracker('root_endpoint') if PerformanceTracker else asyncio.nullcontext():
        
        # Get system statistics
        db_health = await supabase_service.health_check()
        queue_stats = await queue_service.get_queue_stats()
        cache_stats = await cache_service.get_stats()
        
        return {
            "service": "Baseball Trade AI - Optimized",
            "version": APP_VERSION,
            "status": "operational" if db_health['status'] == 'healthy' else "degraded",
            "timestamp": datetime.now().isoformat(),
            "api_version": "v1",
            "endpoints": {
                "health": f"{API_PREFIX}/health",
                "trades": f"{API_PREFIX}/trades",
                "teams": f"{API_PREFIX}/teams",
                "players": f"{API_PREFIX}/players",
                "docs": "/docs" if os.getenv('ENVIRONMENT') != 'production' else None
            },
            "system_status": {
                "database": db_health['status'],
                "cache": "healthy" if cache_stats['redis_available'] else "memory_only",
                "queue": f"{queue_stats['pending_by_priority']} pending tasks",
                "active_analyses": queue_stats.get('processing_count', 0)
            },
            "features": [
                "Natural language trade requests",
                "Multi-agent AI analysis",
                "Live MLB data integration", 
                "Advanced caching with Redis",
                "Background task processing",
                "Comprehensive health monitoring",
                "Production-grade error handling"
            ]
        }


# Performance endpoint
@app.get(f"{API_PREFIX}/system/performance")
async def get_system_performance():
    """Get detailed system performance metrics"""
    
    if not monitor:
        return {"message": "Performance monitoring not available"}
    
    performance_stats = monitor.get_performance_stats()
    queue_stats = await queue_service.get_queue_stats()
    cache_stats = await cache_service.get_stats()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "api_version": APP_VERSION,
        "performance": performance_stats,
        "queue": queue_stats,
        "cache": cache_stats,
        "uptime_seconds": time.time() - getattr(app, 'start_time', time.time())
    }


# Store application start time
app.start_time = time.time()


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 1))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main_optimized:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        access_log=True,
        server_header=False,  # Don't expose server details
        date_header=False     # Don't expose server time
    )