"""
Baseball Trade AI - Production-Optimized FastAPI Application
Advanced performance optimizations, security, and production-ready features
"""

import asyncio
import json
import logging
import os
import signal
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Import optimized components
from api.v1.routers import trades, teams, players, health
from services.supabase_service import supabase_service
from services.cache_service import cache_service
from services.queue_service import queue_service
from performance_config import monitor, PerformanceTracker
from api.exceptions import TradeAIException

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s:%(lineno)d',
    handlers=[
        logging.FileHandler('app.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application configuration
APP_VERSION = "2.0.0-production"
API_PREFIX = "/api/v1"
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
REQUEST_TIMEOUT = 30  # seconds
SHUTDOWN_TIMEOUT = 30  # seconds for graceful shutdown

# Security configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'false').lower() == 'true'

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds

# Global state management
shutdown_event = asyncio.Event()
startup_time = time.time()
active_connections = 0
request_counter = 0


class ConnectionCounterMiddleware(BaseHTTPMiddleware):
    """Middleware to track active connections and requests"""
    
    async def dispatch(self, request: Request, call_next):
        global active_connections, request_counter
        
        active_connections += 1
        request_counter += 1
        request.state.request_id = str(uuid.uuid4())[:8]
        request.state.start_time = time.time()
        
        try:
            response = await call_next(request)
            return response
        finally:
            active_connections -= 1


class SecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware with rate limiting and request validation"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = {}  # Simple in-memory rate limiter
        
    async def dispatch(self, request: Request, call_next):
        # Rate limiting
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        self.rate_limiter = {
            ip: requests for ip, requests in self.rate_limiter.items()
            if any(req_time > current_time - RATE_LIMIT_WINDOW for req_time in requests)
        }
        
        # Check rate limit
        if client_ip in self.rate_limiter:
            recent_requests = [
                req_time for req_time in self.rate_limiter[client_ip]
                if req_time > current_time - RATE_LIMIT_WINDOW
            ]
            if len(recent_requests) >= RATE_LIMIT_REQUESTS:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "RATE_LIMITED",
                        "message": f"Too many requests. Limit: {RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}s",
                        "retry_after": RATE_LIMIT_WINDOW,
                        "timestamp": datetime.now().isoformat()
                    },
                    headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
                )
            self.rate_limiter[client_ip] = recent_requests + [current_time]
        else:
            self.rate_limiter[client_ip] = [current_time]
        
        # Request size validation
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "REQUEST_TOO_LARGE",
                    "message": f"Request size exceeds {MAX_REQUEST_SIZE} bytes",
                    "max_size": MAX_REQUEST_SIZE
                }
            )
        
        # Add security headers and process request
        response = await call_next(request)
        
        # Add comprehensive security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Request-ID": request.state.request_id,
            "X-Rate-Limit-Remaining": str(RATE_LIMIT_REQUESTS - len(self.rate_limiter.get(client_ip, []))),
            "X-Rate-Limit-Reset": str(int(current_time + RATE_LIMIT_WINDOW))
        })
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Advanced performance monitoring and optimization middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate performance metrics
        process_time = time.time() - start_time
        
        # Track performance metrics
        if monitor:
            endpoint = f"{request.method} {request.url.path}"
            await monitor.track_request(endpoint, process_time)
        
        # Add performance headers
        response.headers.update({
            "X-Process-Time": f"{process_time * 1000:.2f}ms",
            "X-API-Version": APP_VERSION,
            "X-Uptime": f"{time.time() - startup_time:.0f}s"
        })
        
        # Add dynamic cache control
        if request.url.path.startswith(f"{API_PREFIX}/teams"):
            response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
        elif request.url.path.startswith(f"{API_PREFIX}/players"):
            response.headers["Cache-Control"] = "public, max-age=180"  # 3 minutes
        elif request.method == "GET" and "status" not in request.url.path:
            response.headers["Cache-Control"] = "public, max-age=60"   # 1 minute
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        # Log slow requests
        if process_time > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s "
                f"[Request ID: {request.state.request_id}]"
            )
        
        return response


# Advanced dependency injection
class DatabaseDependency:
    """Database connection dependency with connection pooling"""
    
    def __init__(self):
        self.pool = None
    
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            # Initialize connection pool if not exists
            self.pool = await supabase_service.get_connection_pool()
        return self.pool


class CacheDependency:
    """Cache dependency with automatic fallback"""
    
    async def get_cache(self):
        """Get cache service with health check"""
        try:
            stats = await cache_service.get_stats()
            if stats['enabled']:
                return cache_service
        except Exception as e:
            logger.warning(f"Cache service unavailable: {e}")
        return None


# Authentication dependency
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Enhanced authentication dependency"""
    if not ENABLE_AUTH:
        return {"user_id": "anonymous", "role": "user"}
    
    if not credentials:
        return None
    
    try:
        # In production, implement proper JWT validation
        # For now, basic validation
        token = credentials.credentials
        if len(token) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Mock user validation - implement real JWT validation in production
        return {
            "user_id": f"user_{token[:8]}",
            "role": "authenticated",
            "token": token
        }
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Advanced application lifecycle management"""
    
    # Startup
    logger.info(f"Starting Baseball Trade AI {APP_VERSION}")
    
    # Initialize services with proper error handling
    try:
        await initialize_services()
        await start_background_services()
        setup_signal_handlers()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Initiating graceful shutdown...")
    await graceful_shutdown()
    logger.info("Shutdown completed")


async def initialize_services():
    """Initialize all application services with health checks"""
    
    # Database initialization
    db_health = await supabase_service.health_check()
    if db_health['status'] != 'healthy':
        logger.warning(f"Database health check warning: {db_health}")
    else:
        logger.info(f"Database connected - {db_health.get('teams_count', 0)} teams available")
    
    # Cache service initialization
    cache_stats = await cache_service.get_stats()
    logger.info(f"Cache service initialized - Redis: {cache_stats['redis_available']}")
    
    # Queue service initialization
    queue_stats = await queue_service.get_queue_stats()
    logger.info(f"Queue service ready - {queue_stats.get('total_tasks', 0)} total tasks")
    
    # Warm critical caches
    try:
        await cache_service.warm_cache()
        logger.info("Cache warming completed")
    except Exception as e:
        logger.warning(f"Cache warming failed: {e}")


async def start_background_services():
    """Start background services and periodic tasks"""
    
    # Start periodic maintenance tasks
    asyncio.create_task(periodic_maintenance())
    asyncio.create_task(metrics_collection())
    
    logger.info("Background services started")


async def graceful_shutdown():
    """Graceful shutdown with timeout"""
    
    # Signal shutdown to all services
    shutdown_event.set()
    
    # Wait for active requests to complete (with timeout)
    shutdown_start = time.time()
    while active_connections > 0 and (time.time() - shutdown_start) < SHUTDOWN_TIMEOUT:
        logger.info(f"Waiting for {active_connections} active connections...")
        await asyncio.sleep(1)
    
    # Force shutdown remaining connections
    if active_connections > 0:
        logger.warning(f"Force closing {active_connections} remaining connections")
    
    # Shutdown services
    await queue_service.shutdown()
    
    # Close cache connections
    if hasattr(cache_service, 'redis_client') and cache_service.redis_client:
        try:
            await cache_service.redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    logger.info("Graceful shutdown completed")


def setup_signal_handlers():
    """Setup system signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(graceful_shutdown())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


async def periodic_maintenance():
    """Periodic maintenance tasks"""
    
    while not shutdown_event.is_set():
        try:
            # Cache cleanup
            if hasattr(cache_service, '_cleanup_memory_cache'):
                await cache_service._cleanup_memory_cache()
            
            # Queue maintenance
            await queue_service.cleanup_completed_tasks()
            
            logger.debug("Periodic maintenance completed")
            
            # Wait for next maintenance cycle (1 hour) or shutdown
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=3600)
                break
            except asyncio.TimeoutError:
                continue
                
        except Exception as e:
            logger.error(f"Periodic maintenance error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry


async def metrics_collection():
    """Collect and log system metrics"""
    
    while not shutdown_event.is_set():
        try:
            if monitor:
                stats = monitor.get_performance_stats()
                logger.info(f"Performance stats: {stats}")
            
            # Wait for next collection cycle (15 minutes) or shutdown
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=900)
                break
            except asyncio.TimeoutError:
                continue
                
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            await asyncio.sleep(300)


# Create optimized FastAPI application
app = FastAPI(
    title="Baseball Trade AI - Production",
    description="Production-optimized MLB trade analysis API with AI agents",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if os.getenv('ENVIRONMENT') != 'production' else None,
    redoc_url="/redoc" if os.getenv('ENVIRONMENT') != 'production' else None,
    openapi_url="/openapi.json" if os.getenv('ENVIRONMENT') != 'production' else None
)

# Add middleware stack (order matters!)
app.add_middleware(ConnectionCounterMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=[
        "x-rate-limit-remaining", 
        "x-rate-limit-reset",
        "x-process-time",
        "x-request-id"
    ]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=500)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS + ['*'] if os.getenv('ENVIRONMENT') == 'development' else ALLOWED_HOSTS
)


# Advanced exception handlers
@app.exception_handler(TradeAIException)
async def trade_ai_exception_handler(request: Request, exc: TradeAIException):
    """Handle custom Trade AI exceptions"""
    logger.error(f"Trade AI Exception: {exc.message} [Request ID: {getattr(request.state, 'request_id', 'unknown')}]")
    
    if monitor:
        await monitor.track_error(exc.__class__.__name__)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc} [Request ID: {getattr(request.state, 'request_id', 'unknown')}]")
    
    if monitor:
        await monitor.track_error("ValidationError")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                }
                for error in exc.errors()
            ],
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} [Request ID: {getattr(request.state, 'request_id', 'unknown')}]")
    
    if monitor:
        await monitor.track_error(f"HTTP_{exc.status_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        f"Unexpected error: {exc} [Request ID: {getattr(request.state, 'request_id', 'unknown')}]", 
        exc_info=True
    )
    
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
            "request_id": getattr(request.state, 'request_id', None),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


# Include API routers with dependencies
app.include_router(
    health.router, 
    prefix=API_PREFIX, 
    tags=["Health"],
    dependencies=[Depends(DatabaseDependency().get_connection)]
)
app.include_router(
    trades.router, 
    prefix=API_PREFIX, 
    tags=["Trades"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    teams.router, 
    prefix=API_PREFIX, 
    tags=["Teams"],
    dependencies=[Depends(CacheDependency().get_cache)]
)
app.include_router(
    players.router, 
    prefix=API_PREFIX, 
    tags=["Players"],
    dependencies=[Depends(CacheDependency().get_cache)]
)


# Root endpoint with comprehensive system information
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Production API root endpoint with detailed system status"""
    
    async with PerformanceTracker('root_endpoint') if PerformanceTracker else asyncio.nullcontext():
        
        # Get system statistics
        db_health = await supabase_service.health_check()
        queue_stats = await queue_service.get_queue_stats()
        cache_stats = await cache_service.get_stats()
        
        uptime_seconds = time.time() - startup_time
        
        return {
            "service": "Baseball Trade AI - Production",
            "version": APP_VERSION,
            "status": "operational" if db_health['status'] == 'healthy' else "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime": {
                "seconds": int(uptime_seconds),
                "formatted": str(timedelta(seconds=int(uptime_seconds)))
            },
            "api": {
                "version": "v1",
                "prefix": API_PREFIX,
                "docs": "/docs" if os.getenv('ENVIRONMENT') != 'production' else None,
                "total_requests": request_counter,
                "active_connections": active_connections
            },
            "system_status": {
                "database": db_health['status'],
                "cache": "redis" if cache_stats['redis_available'] else "memory",
                "queue": f"{queue_stats.get('pending_by_priority', {})} pending",
                "active_analyses": queue_stats.get('processing_count', 0),
                "rate_limit": f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}s"
            },
            "features": [
                "Natural language trade requests",
                "Multi-agent AI analysis",
                "Live MLB data integration",
                "Advanced Redis caching",
                "Background task processing",
                "Real-time progress tracking",
                "Comprehensive monitoring",
                "Production security headers",
                "Request rate limiting",
                "Graceful shutdown support"
            ],
            "endpoints": {
                "health": f"{API_PREFIX}/health",
                "trades": f"{API_PREFIX}/trades",
                "teams": f"{API_PREFIX}/teams", 
                "players": f"{API_PREFIX}/players",
                "metrics": f"{API_PREFIX}/system/metrics"
            }
        }


# System metrics endpoint
@app.get(f"{API_PREFIX}/system/metrics")
async def get_system_metrics(
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Detailed system metrics endpoint"""
    
    if not monitor:
        return {"message": "Performance monitoring not available"}
    
    # Get comprehensive metrics
    performance_stats = monitor.get_performance_stats()
    queue_stats = await queue_service.get_queue_stats()
    cache_stats = await cache_service.get_stats()
    
    uptime_seconds = time.time() - startup_time
    
    return {
        "timestamp": datetime.now().isoformat(),
        "api_version": APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "system": {
            "total_requests": request_counter,
            "active_connections": active_connections,
            "memory_usage_mb": cache_stats.get('memory_cache_size', 0),
            "rate_limit_config": {
                "requests_per_window": RATE_LIMIT_REQUESTS,
                "window_seconds": RATE_LIMIT_WINDOW
            }
        },
        "performance": performance_stats,
        "queue": queue_stats,
        "cache": cache_stats,
        "user": current_user
    }


# Response streaming endpoint for large datasets
@app.get(f"{API_PREFIX}/stream/teams")
async def stream_teams_data():
    """Stream teams data for large responses"""
    
    async def generate_teams_stream():
        """Generate streaming response for teams data"""
        try:
            teams = await supabase_service.get_all_teams()
            
            # Stream response with proper JSON formatting
            yield '{"teams": ['
            
            for i, team in enumerate(teams):
                if i > 0:
                    yield ','
                yield json.dumps(team)
                # Small delay to demonstrate streaming
                await asyncio.sleep(0.01)
            
            yield '], "total": '
            yield str(len(teams))
            yield ', "streamed": true, "timestamp": "'
            yield datetime.now().isoformat()
            yield '"}'
            
        except Exception as e:
            logger.error(f"Error streaming teams data: {e}")
            yield '{"error": "Stream error", "message": "' + str(e) + '"}'
    
    return StreamingResponse(
        generate_teams_stream(),
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


if __name__ == "__main__":
    # Production server configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 1))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting production server on {host}:{port} with {workers} workers")
    
    # Production uvicorn configuration
    uvicorn.run(
        "main_production:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        access_log=True,
        server_header=False,
        date_header=False,
        loop="uvloop" if os.name != "nt" else "asyncio",  # Use uvloop on Unix
        http="httptools",  # Use httptools parser
        limit_max_requests=10000,  # Restart workers after 10k requests
        timeout_keep_alive=120,  # Keep-alive timeout
        timeout_graceful_shutdown=SHUTDOWN_TIMEOUT
    )