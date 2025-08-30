"""
Production-ready configuration for Baseball Trade AI FastAPI application
Implements security hardening and performance optimizations
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import time
import os
from typing import List
import logging

logger = logging.getLogger(__name__)

class ProductionConfig:
    """Production configuration settings"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.allowed_hosts = self._get_allowed_hosts()
        self.cors_origins = self._get_cors_origins()
        self.debug = self.environment == 'development'
        
    def _get_allowed_hosts(self) -> List[str]:
        """Get allowed hosts for the application"""
        if self.environment == 'production':
            return [
                "api.baseballtradeai.com",
                "*.vercel.app",
                "localhost:8000"
            ]
        return ["*"]  # Allow all in development
        
    def _get_cors_origins(self) -> List[str]:
        """Get CORS origins"""
        if self.environment == 'production':
            return [
                "https://baseballtradeai.com",
                "https://www.baseballtradeai.com", 
                "https://baseballtradeai.vercel.app",
            ]
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001"
        ]

def configure_security_middleware(app: FastAPI, config: ProductionConfig):
    """Configure security middleware for production"""
    
    # Trusted host middleware (protects against Host header attacks)
    if config.environment == 'production':
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=config.allowed_hosts
        )
    
    # CORS middleware with restricted origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID"
        ],
        expose_headers=["X-Request-ID", "X-Process-Time"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

def configure_performance_middleware(app: FastAPI):
    """Configure performance optimization middleware"""
    
    # Gzip compression for responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Cache control for API responses
        if request.url.path.startswith("/api/teams"):
            response.headers["Cache-Control"] = "public, max-age=3600"  # Cache teams for 1 hour
        elif request.url.path.startswith("/api/analysis"):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"  # Don't cache analysis results
        else:
            response.headers["Cache-Control"] = "no-cache"
            
        return response
    
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Add processing time header for monitoring"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(f"{process_time:.4f}")
        return response

def configure_content_security_policy(app: FastAPI, config: ProductionConfig):
    """Configure Content Security Policy"""
    
    @app.middleware("http")
    async def add_csp_header(request: Request, call_next):
        """Add Content Security Policy header"""
        response = await call_next(request)
        
        if config.environment == 'production':
            csp = (
                "default-src 'none'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://api.openai.com https://supabase.co; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # More permissive CSP for development
            csp = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "connect-src 'self' http://localhost:* ws://localhost:* https:;"
            )
            
        response.headers["Content-Security-Policy"] = csp
        return response

def configure_rate_limiting(app: FastAPI):
    """Configure rate limiting middleware"""
    from collections import defaultdict, deque
    import asyncio
    from fastapi import HTTPException, status
    
    # Simple in-memory rate limiter (use Redis in production)
    request_counts = defaultdict(deque)
    
    @app.middleware("http") 
    async def rate_limiting_middleware(request: Request, call_next):
        """Basic rate limiting based on IP address"""
        
        client_ip = request.client.host
        current_time = time.time()
        
        # Define rate limits per endpoint
        rate_limits = {
            "/api/analyze-trade": {"requests": 3, "window": 60},  # 3 per minute
            "/api/quick-analysis": {"requests": 10, "window": 60},  # 10 per minute
            "default": {"requests": 100, "window": 60}  # 100 per minute for other endpoints
        }
        
        # Get rate limit for current path
        endpoint = request.url.path
        limit_config = rate_limits.get(endpoint, rate_limits["default"])
        
        # Clean old requests
        window_start = current_time - limit_config["window"]
        while request_counts[client_ip] and request_counts[client_ip][0] < window_start:
            request_counts[client_ip].popleft()
        
        # Check if rate limit exceeded
        if len(request_counts[client_ip]) >= limit_config["requests"]:
            retry_after = int(limit_config["window"] - (current_time - request_counts[client_ip][0]))
            
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            
            response = Response(
                content='{"error": "Rate limit exceeded", "retry_after": ' + str(retry_after) + '}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit_config["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after))
                }
            )
            return response
        
        # Add current request
        request_counts[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = limit_config["requests"] - len(request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + limit_config["window"]))
        
        return response

def configure_request_logging(app: FastAPI, config: ProductionConfig):
    """Configure request logging middleware"""
    import uuid
    
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Log requests and responses"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"REQUEST {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "")[:200]
            }
        )
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response  
            logger.info(
                f"RESPONSE {request_id}: {response.status_code} ({duration:.3f}s)",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"ERROR {request_id}: {str(e)} ({duration:.3f}s)",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

def create_production_app() -> FastAPI:
    """Create production-ready FastAPI application"""
    
    config = ProductionConfig()
    
    app = FastAPI(
        title="Baseball Trade AI - Production",
        description="Production-ready MLB trade analysis API",
        version="2.0.0",
        debug=config.debug,
        docs_url="/docs" if config.debug else None,  # Disable docs in production
        redoc_url="/redoc" if config.debug else None,
    )
    
    # Configure middleware in order (important!)
    configure_security_middleware(app, config)
    configure_performance_middleware(app)
    configure_content_security_policy(app, config)
    configure_rate_limiting(app)
    configure_request_logging(app, config)
    
    return app

# Authentication setup (basic structure for future implementation)
security = HTTPBearer(auto_error=False)

async def get_current_user(request: Request):
    """Get current user from request (placeholder for authentication)"""
    # TODO: Implement actual authentication
    # For now, return a mock user in development
    if os.getenv('ENVIRONMENT') == 'development':
        return {"user_id": "dev-user", "role": "user"}
    
    # In production, validate JWT token
    authorization = request.headers.get("Authorization")
    if authorization:
        # TODO: Validate JWT token
        pass
    
    return None

def require_auth(require_admin: bool = False):
    """Decorator to require authentication"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            if require_admin and user.get("role") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            
            request.state.current_user = user
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator