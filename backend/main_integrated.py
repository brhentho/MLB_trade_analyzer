"""
Baseball Trade AI - Integrated Production System
Final optimized FastAPI application with all systems integrated
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
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import optimized components with fallbacks
try:
    from api.v1.routers.trades import router as trades_router
    from api.v1.routers.teams import router as teams_router  
    from api.v1.routers.players import router as players_router
    from api.v1.routers.enhanced_health import router as health_router
except ImportError:
    # Fallback imports
    trades_router = None
    teams_router = None
    players_router = None
    health_router = None

try:
    from services.supabase_service import supabase_service, TradeAnalysisRecord
    from services.cache_service import cache_service
    from services.queue_service import queue_service
    from services.optimized_database_service import DatabaseService
except ImportError:
    supabase_service = None
    cache_service = None
    queue_service = None
    DatabaseService = None

try:
    from core.performance import PerformanceTracker
    from core.logging_config import setup_logging
    from middleware.monitoring import MonitoringMiddleware
except ImportError:
    PerformanceTracker = None
    setup_logging = None
    MonitoringMiddleware = None

try:
    from api.exceptions import TradeAIException, handle_trade_ai_exception
except ImportError:
    TradeAIException = Exception
    handle_trade_ai_exception = None

# Configure logging
if setup_logging:
    setup_logging()
else:
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
APP_VERSION = "2.1.0-integrated"
API_PREFIX = "/api/v1"
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
REQUEST_TIMEOUT = 30
SHUTDOWN_TIMEOUT = 30

# Security configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'false').lower() == 'true'

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))

# Global state management
shutdown_event = asyncio.Event()
startup_time = time.time()
active_connections = 0
request_counter = 0

# Database service instance
database_service = DatabaseService() if DatabaseService else None


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


class IntegratedSecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware with integrated rate limiting and validation"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = {}
        
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
        
        # Process request and add security headers
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


class IntegratedPerformanceMiddleware(BaseHTTPMiddleware):
    """Performance monitoring and caching middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Calculate performance metrics
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers.update({
            "X-Process-Time": f"{process_time * 1000:.2f}ms",
            "X-API-Version": APP_VERSION,
            "X-Uptime": f"{time.time() - startup_time:.0f}s"
        })
        
        # Dynamic cache control
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


# Authentication dependency
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Enhanced authentication dependency with integrated validation"""
    if not ENABLE_AUTH:
        return {"user_id": "anonymous", "role": "user"}
    
    if not credentials:
        return None
    
    try:
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
    """Integrated application lifecycle management"""
    
    # Startup
    logger.info(f"Starting Baseball Trade AI {APP_VERSION}")
    
    try:
        await initialize_integrated_services()
        await start_background_services()
        setup_signal_handlers()
        logger.info("Integrated application startup completed successfully")
    except Exception as e:
        logger.error(f"Integrated startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Initiating integrated graceful shutdown...")
    await graceful_integrated_shutdown()
    logger.info("Integrated shutdown completed")


async def initialize_integrated_services():
    """Initialize all integrated services with health checks"""
    
    # Database initialization
    if supabase_service:
        db_health = await supabase_service.health_check()
        if db_health['status'] != 'healthy':
            logger.warning(f"Database health check warning: {db_health}")
        else:
            logger.info(f"Database connected - {db_health.get('teams_count', 0)} teams available")
    
    # Optimized database service
    if database_service:
        await database_service.initialize()
        logger.info("Optimized database service initialized")
    
    # Cache service initialization
    if cache_service:
        cache_stats = await cache_service.get_stats()
        logger.info(f"Cache service initialized - Redis: {cache_stats['redis_available']}")
        
        # Warm critical caches
        try:
            await cache_service.warm_cache()
            logger.info("Cache warming completed")
        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")
    
    # Queue service initialization
    if queue_service:
        queue_stats = await queue_service.get_queue_stats()
        logger.info(f"Queue service ready - {queue_stats.get('total_tasks', 0)} total tasks")


async def start_background_services():
    """Start integrated background services"""
    
    # Start periodic maintenance
    asyncio.create_task(integrated_periodic_maintenance())
    asyncio.create_task(integrated_metrics_collection())
    
    logger.info("Integrated background services started")


async def graceful_integrated_shutdown():
    """Graceful shutdown with integrated service cleanup"""
    
    shutdown_event.set()
    
    # Wait for active requests
    shutdown_start = time.time()
    while active_connections > 0 and (time.time() - shutdown_start) < SHUTDOWN_TIMEOUT:
        logger.info(f"Waiting for {active_connections} active connections...")
        await asyncio.sleep(1)
    
    if active_connections > 0:
        logger.warning(f"Force closing {active_connections} remaining connections")
    
    # Shutdown services
    if queue_service:
        await queue_service.shutdown()
    
    if database_service:
        await database_service.close()
    
    # Close cache connections
    if cache_service and hasattr(cache_service, 'redis_client') and cache_service.redis_client:
        try:
            await cache_service.redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    logger.info("Integrated graceful shutdown completed")


def setup_signal_handlers():
    """Setup system signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(graceful_integrated_shutdown())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


async def integrated_periodic_maintenance():
    """Integrated periodic maintenance tasks"""
    
    while not shutdown_event.is_set():
        try:
            # Cache cleanup
            if cache_service and hasattr(cache_service, '_cleanup_memory_cache'):
                await cache_service._cleanup_memory_cache()
            
            # Queue maintenance
            if queue_service:
                await queue_service.cleanup_completed_tasks()
            
            # Database maintenance
            if database_service:
                await database_service.cleanup_old_records()
            
            logger.debug("Integrated periodic maintenance completed")
            
            # Wait for next maintenance cycle
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=3600)  # 1 hour
                break
            except asyncio.TimeoutError:
                continue
                
        except Exception as e:
            logger.error(f"Integrated periodic maintenance error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry


async def integrated_metrics_collection():
    """Collect and log integrated system metrics"""
    
    while not shutdown_event.is_set():
        try:
            metrics = {}
            
            # Database metrics
            if database_service:
                metrics['database'] = await database_service.get_metrics()
            
            # Cache metrics
            if cache_service:
                metrics['cache'] = await cache_service.get_stats()
            
            # Queue metrics
            if queue_service:
                metrics['queue'] = await queue_service.get_queue_stats()
            
            # System metrics
            metrics['system'] = {
                'uptime_seconds': time.time() - startup_time,
                'total_requests': request_counter,
                'active_connections': active_connections
            }
            
            logger.info(f"Integrated metrics: {metrics}")
            
            # Wait for next collection cycle
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=900)  # 15 minutes
                break
            except asyncio.TimeoutError:
                continue
                
        except Exception as e:
            logger.error(f"Integrated metrics collection error: {e}")
            await asyncio.sleep(300)


# Create integrated FastAPI application
app = FastAPI(
    title="Baseball Trade AI - Integrated Production",
    description="Fully integrated MLB trade analysis API with optimized performance",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if os.getenv('ENVIRONMENT') != 'production' else None,
    redoc_url="/redoc" if os.getenv('ENVIRONMENT') != 'production' else None,
    openapi_url="/openapi.json" if os.getenv('ENVIRONMENT') != 'production' else None
)

# Add middleware stack (order matters!)
app.add_middleware(ConnectionCounterMiddleware)
app.add_middleware(IntegratedPerformanceMiddleware)
app.add_middleware(IntegratedSecurityMiddleware)

# Add monitoring middleware if available
if MonitoringMiddleware:
    app.add_middleware(MonitoringMiddleware)

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


# Exception handlers
if handle_trade_ai_exception:
    @app.exception_handler(TradeAIException)
    async def trade_ai_exception_handler(request: Request, exc: TradeAIException):
        return await handle_trade_ai_exception(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc} [Request ID: {getattr(request.state, 'request_id', 'unknown')}]")
    
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


# Include routers if available
if health_router:
    app.include_router(health_router, prefix=API_PREFIX, tags=["Health"])
if trades_router:
    app.include_router(trades_router, prefix=API_PREFIX, tags=["Trades"])
if teams_router:
    app.include_router(teams_router, prefix=API_PREFIX, tags=["Teams"])
if players_router:
    app.include_router(players_router, prefix=API_PREFIX, tags=["Players"])


# Fallback Request/Response Models
class TradeRequest(BaseModel):
    team: str = Field(..., min_length=2, max_length=50)
    request: str = Field(..., min_length=10, max_length=1000)
    urgency: Optional[str] = Field('medium', description="Urgency level")
    budget_limit: Optional[float] = Field(None, ge=0, le=500000000)
    include_prospects: bool = Field(True)
    max_trade_partners: int = Field(2, ge=1, le=4)


# Root endpoint with comprehensive system information
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Integrated production API root endpoint with full system status"""
    
    try:
        # Get system statistics
        system_stats = {}
        
        if supabase_service:
            db_health = await supabase_service.health_check()
            system_stats['database'] = db_health
        
        if cache_service:
            cache_stats = await cache_service.get_stats()
            system_stats['cache'] = cache_stats
        
        if queue_service:
            queue_stats = await queue_service.get_queue_stats()
            system_stats['queue'] = queue_stats
        
        if database_service:
            db_metrics = await database_service.get_metrics()
            system_stats['optimized_database'] = db_metrics
        
        uptime_seconds = time.time() - startup_time
        
        return {
            "service": "Baseball Trade AI - Integrated Production",
            "version": APP_VERSION,
            "status": "operational",
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
            "integrated_features": [
                "Unified service architecture",
                "Optimized database connections",
                "Advanced Redis caching",
                "Background task processing",
                "Real-time progress tracking",
                "Comprehensive monitoring",
                "Production security headers",
                "Request rate limiting",
                "Graceful shutdown support",
                "Health check integration",
                "Performance optimization",
                "Error tracking and logging"
            ],
            "system_status": system_stats,
            "endpoints": {
                "health": f"{API_PREFIX}/health",
                "trades": f"{API_PREFIX}/trades",
                "teams": f"{API_PREFIX}/teams",
                "players": f"{API_PREFIX}/players",
                "metrics": f"{API_PREFIX}/system/metrics"
            }
        }
    
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        return {
            "service": "Baseball Trade AI - Integrated Production",
            "version": APP_VERSION,
            "status": "degraded",
            "error": "Some services may be unavailable",
            "timestamp": datetime.now().isoformat()
        }


# System health endpoint
@app.get(f"{API_PREFIX}/health")
async def integrated_health_check():
    """Comprehensive integrated health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": APP_VERSION,
            "uptime_seconds": int(time.time() - startup_time),
            "services": {}
        }
        
        # Check each service
        services_healthy = True
        
        if supabase_service:
            try:
                db_health = await supabase_service.health_check()
                health_status["services"]["database"] = db_health
                if db_health.get('status') != 'healthy':
                    services_healthy = False
            except Exception as e:
                health_status["services"]["database"] = {"status": "error", "error": str(e)}
                services_healthy = False
        
        if cache_service:
            try:
                cache_stats = await cache_service.get_stats()
                health_status["services"]["cache"] = {"status": "healthy", **cache_stats}
            except Exception as e:
                health_status["services"]["cache"] = {"status": "error", "error": str(e)}
                services_healthy = False
        
        if queue_service:
            try:
                queue_stats = await queue_service.get_queue_stats()
                health_status["services"]["queue"] = {"status": "healthy", **queue_stats}
            except Exception as e:
                health_status["services"]["queue"] = {"status": "error", "error": str(e)}
                services_healthy = False
        
        if database_service:
            try:
                db_metrics = await database_service.get_metrics()
                health_status["services"]["optimized_database"] = {"status": "healthy", **db_metrics}
            except Exception as e:
                health_status["services"]["optimized_database"] = {"status": "error", "error": str(e)}
                services_healthy = False
        
        # Set overall status
        if not services_healthy:
            health_status["status"] = "degraded"
        
        status_code = 200 if services_healthy else 503
        return JSONResponse(status_code=status_code, content=health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# System metrics endpoint
@app.get(f"{API_PREFIX}/system/metrics")
async def get_integrated_metrics(
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Comprehensive integrated system metrics"""
    
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "api_version": APP_VERSION,
            "uptime_seconds": time.time() - startup_time,
            "system": {
                "total_requests": request_counter,
                "active_connections": active_connections,
                "rate_limit_config": {
                    "requests_per_window": RATE_LIMIT_REQUESTS,
                    "window_seconds": RATE_LIMIT_WINDOW
                }
            }
        }
        
        # Add service metrics
        if cache_service:
            metrics["cache"] = await cache_service.get_stats()
        
        if queue_service:
            metrics["queue"] = await queue_service.get_queue_stats()
        
        if database_service:
            metrics["database"] = await database_service.get_metrics()
        
        if supabase_service:
            db_health = await supabase_service.health_check()
            metrics["supabase"] = db_health
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": "Failed to get system metrics", "message": str(e)}


# Fallback trade analysis endpoint (if routers not available)
if not trades_router:
    @app.post(f"{API_PREFIX}/trades/analyze")
    async def fallback_analyze_trade(
        request: TradeRequest,
        background_tasks: BackgroundTasks
    ):
        """Fallback trade analysis endpoint"""
        return {
            "message": "Trade analysis endpoint available",
            "team": request.team,
            "request": request.request,
            "status": "fallback_mode",
            "note": "Full trade analysis requires complete router integration"
        }


if __name__ == "__main__":
    # Integrated production server configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 1))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting integrated production server on {host}:{port} with {workers} workers")
    
    # Production uvicorn configuration
    uvicorn.run(
        "main_integrated:app",
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
