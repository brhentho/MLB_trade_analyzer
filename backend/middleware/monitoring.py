"""
Advanced Middleware Stack for Baseball Trade AI
Performance monitoring, request tracing, error handling, and observability
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Tuple
from contextlib import asynccontextmanager

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send

logger = logging.getLogger(__name__)

# Configuration
ENABLE_DETAILED_LOGGING = os.getenv('ENABLE_DETAILED_LOGGING', 'true').lower() == 'true'
ENABLE_REQUEST_TRACING = os.getenv('ENABLE_REQUEST_TRACING', 'true').lower() == 'true'
ENABLE_PERFORMANCE_TRACKING = os.getenv('ENABLE_PERFORMANCE_TRACKING', 'true').lower() == 'true'
SLOW_REQUEST_THRESHOLD = float(os.getenv('SLOW_REQUEST_THRESHOLD', '1.0'))
LOG_REQUEST_BODY = os.getenv('LOG_REQUEST_BODY', 'false').lower() == 'true'
MAX_BODY_LOG_SIZE = int(os.getenv('MAX_BODY_LOG_SIZE', '1024'))


class RequestTracker:
    """Advanced request tracking and analytics"""
    
    def __init__(self):
        self.active_requests: Dict[str, Dict] = {}
        self.request_history: List[Dict] = []
        self.error_patterns: Dict[str, int] = {}
        self.endpoint_stats: Dict[str, Dict] = {}
        
    def start_request(self, request_id: str, request: Request) -> Dict:
        """Start tracking a request"""
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "start_time": time.time(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.active_requests[request_id] = request_info
        return request_info
    
    def end_request(
        self, 
        request_id: str, 
        response: Response, 
        error: Optional[Exception] = None
    ) -> Optional[Dict]:
        """End request tracking and collect metrics"""
        if request_id not in self.active_requests:
            return None
        
        request_info = self.active_requests.pop(request_id)
        end_time = time.time()
        duration = end_time - request_info["start_time"]
        
        # Build completion info
        completion_info = {
            **request_info,
            "end_time": end_time,
            "duration_ms": round(duration * 1000, 2),
            "status_code": response.status_code if response else 500,
            "response_size": len(response.body) if hasattr(response, 'body') and response.body else 0,
            "error": str(error) if error else None,
            "error_type": error.__class__.__name__ if error else None
        }
        
        # Update endpoint statistics
        endpoint_key = f"{request_info['method']} {request_info['path']}"
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                "total_requests": 0,
                "total_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
                "error_count": 0,
                "status_codes": {}
            }
        
        stats = self.endpoint_stats[endpoint_key]
        stats["total_requests"] += 1
        stats["total_duration"] += duration
        stats["min_duration"] = min(stats["min_duration"], duration)
        stats["max_duration"] = max(stats["max_duration"], duration)
        
        status_code = completion_info["status_code"]
        stats["status_codes"][status_code] = stats["status_codes"].get(status_code, 0) + 1
        
        if error or (status_code >= 400):
            stats["error_count"] += 1
            
            # Track error patterns
            error_pattern = f"{status_code}:{error.__class__.__name__}" if error else f"{status_code}:HTTP_ERROR"
            self.error_patterns[error_pattern] = self.error_patterns.get(error_pattern, 0) + 1
        
        # Add to history (keep last 1000 requests)
        self.request_history.append(completion_info)
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
        
        return completion_info
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive request statistics"""
        total_requests = sum(stats["total_requests"] for stats in self.endpoint_stats.values())
        
        return {
            "active_requests": len(self.active_requests),
            "total_requests": total_requests,
            "endpoint_stats": {
                endpoint: {
                    **stats,
                    "avg_duration": stats["total_duration"] / stats["total_requests"] if stats["total_requests"] > 0 else 0,
                    "error_rate": stats["error_count"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
                }
                for endpoint, stats in self.endpoint_stats.items()
            },
            "error_patterns": self.error_patterns,
            "recent_errors": [
                req for req in self.request_history[-50:]  # Last 50 requests
                if req.get("error") or req.get("status_code", 200) >= 400
            ]
        }
    
    def get_slow_requests(self, threshold: float = None) -> List[Dict]:
        """Get requests that exceeded duration threshold"""
        threshold = threshold or SLOW_REQUEST_THRESHOLD
        return [
            req for req in self.request_history
            if req.get("duration_ms", 0) / 1000 > threshold
        ]


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Advanced performance monitoring middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_tracker = RequestTracker()
        self.performance_alerts: List[Dict] = []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch with comprehensive monitoring"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Start request tracking
        request_info = self.request_tracker.start_request(request_id, request)
        
        # Log request start
        if ENABLE_DETAILED_LOGGING:
            logger.info(
                f"Request started: {request.method} {request.url.path} "
                f"[ID: {request_id}] [IP: {request.client.host}]"
            )
        
        # Log request body if enabled (be careful with sensitive data)
        if LOG_REQUEST_BODY and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) <= MAX_BODY_LOG_SIZE:
                    logger.debug(f"Request body [{request_id}]: {body.decode()[:MAX_BODY_LOG_SIZE]}")
            except Exception as e:
                logger.warning(f"Could not log request body [{request_id}]: {e}")
        
        error = None
        response = None
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{(time.time() - request.state.start_time) * 1000:.2f}ms"
            
            return response
            
        except Exception as e:
            error = e
            logger.error(f"Request error [{request_id}]: {e}", exc_info=True)
            raise
            
        finally:
            # End request tracking
            completion_info = self.request_tracker.end_request(request_id, response, error)
            
            if completion_info:
                duration = completion_info["duration_ms"] / 1000
                
                # Log completion
                if ENABLE_DETAILED_LOGGING:
                    log_level = logging.WARNING if duration > SLOW_REQUEST_THRESHOLD else logging.INFO
                    logger.log(
                        log_level,
                        f"Request completed: {request.method} {request.url.path} "
                        f"[ID: {request_id}] [Duration: {duration:.3f}s] "
                        f"[Status: {completion_info.get('status_code', 'unknown')}]"
                    )
                
                # Performance alerts
                if duration > SLOW_REQUEST_THRESHOLD:
                    alert = {
                        "type": "slow_request",
                        "request_id": request_id,
                        "endpoint": f"{request.method} {request.url.path}",
                        "duration": duration,
                        "threshold": SLOW_REQUEST_THRESHOLD,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    self.performance_alerts.append(alert)
                    
                    # Keep only last 100 alerts
                    if len(self.performance_alerts) > 100:
                        self.performance_alerts = self.performance_alerts[-100:]


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Request tracing and correlation middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.trace_contexts: Dict[str, Dict] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add distributed tracing context"""
        
        if not ENABLE_REQUEST_TRACING:
            return await call_next(request)
        
        # Extract or generate trace ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        # Create trace context
        trace_context = {
            "trace_id": trace_id,
            "request_id": request_id,
            "parent_span": request.headers.get("X-Parent-Span"),
            "start_time": time.time(),
            "service": "baseball-trade-ai",
            "operation": f"{request.method} {request.url.path}"
        }
        
        request.state.trace_context = trace_context
        self.trace_contexts[request_id] = trace_context
        
        try:
            response = await call_next(request)
            
            # Add tracing headers to response
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        finally:
            # Clean up trace context
            if request_id in self.trace_contexts:
                trace_context["end_time"] = time.time()
                trace_context["duration"] = trace_context["end_time"] - trace_context["start_time"]
                
                # In production, send to tracing system (Jaeger, Zipkin, etc.)
                if trace_context["duration"] > 0.1:  # Only log traces > 100ms
                    logger.info(f"Trace completed: {trace_context}")
                
                del self.trace_contexts[request_id]


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Advanced error handling and reporting middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.error_stats: Dict[str, int] = {}
        self.recent_errors: List[Dict] = []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enhanced error handling with reporting"""
        
        try:
            return await call_next(request)
            
        except HTTPException as e:
            # Handle known HTTP exceptions
            await self._log_error(request, e, "http_exception")
            raise
            
        except asyncio.TimeoutError as e:
            # Handle timeout errors
            await self._log_error(request, e, "timeout_error")
            raise HTTPException(
                status_code=504,
                detail="Request timeout - please try again"
            )
            
        except ConnectionError as e:
            # Handle connection errors
            await self._log_error(request, e, "connection_error")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable"
            )
            
        except Exception as e:
            # Handle unexpected errors
            await self._log_error(request, e, "unexpected_error")
            
            # Don't expose internal errors in production
            if os.getenv('ENVIRONMENT') == 'production':
                raise HTTPException(
                    status_code=500,
                    detail="An internal error occurred"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal error: {str(e)}"
                )
    
    async def _log_error(self, request: Request, error: Exception, error_type: str):
        """Log error with context"""
        
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        error_info = {
            "request_id": request_id,
            "error_type": error_type,
            "error_class": error.__class__.__name__,
            "error_message": str(error),
            "endpoint": f"{request.method} {request.url.path}",
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Update error statistics
        error_key = f"{error_type}:{error.__class__.__name__}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1
        
        # Add to recent errors
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > 100:
            self.recent_errors = self.recent_errors[-100:]
        
        # Log error
        logger.error(
            f"Error in request [{request_id}]: {error.__class__.__name__}: {str(error)}",
            extra={"error_info": error_info},
            exc_info=True
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": self.error_stats,
            "total_errors": sum(self.error_stats.values()),
            "recent_errors": self.recent_errors[-20:]  # Last 20 errors
        }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers and protection middleware"""
    
    def __init__(self, app: ASGIApp, custom_headers: Optional[Dict[str, str]] = None):
        super().__init__(app)
        self.custom_headers = custom_headers or {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add comprehensive security headers"""
        
        response = await call_next(request)
        
        # Default security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "font-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none';"
            ),
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }
        
        # Add custom headers
        security_headers.update(self.custom_headers)
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Advanced response compression middleware"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        minimum_size: int = 500,
        compressible_types: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = compressible_types or [
            "application/json",
            "application/javascript", 
            "text/css",
            "text/html",
            "text/plain",
            "text/xml"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply compression based on content type and size"""
        
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        
        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0]
        if content_type not in self.compressible_types:
            return response
        
        # Check content size
        if hasattr(response, 'body') and response.body:
            if len(response.body) < self.minimum_size:
                return response
            
            # Apply compression (simplified - use proper GZIP in production)
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Vary"] = "Accept-Encoding"
        
        return response


# Middleware factory for easy configuration
def create_monitoring_middleware_stack(
    app: ASGIApp,
    enable_performance: bool = True,
    enable_tracing: bool = True,
    enable_error_handling: bool = True,
    enable_security_headers: bool = True,
    enable_compression: bool = True,
    custom_security_headers: Optional[Dict[str, str]] = None
) -> ASGIApp:
    """Create a comprehensive middleware stack"""
    
    if enable_compression:
        app = CompressionMiddleware(app)
    
    if enable_security_headers:
        app = SecurityHeadersMiddleware(app, custom_security_headers)
    
    if enable_error_handling:
        app = ErrorHandlingMiddleware(app)
    
    if enable_tracing:
        app = RequestTracingMiddleware(app)
    
    if enable_performance:
        app = PerformanceMonitoringMiddleware(app)
    
    return app


# Global instances for accessing middleware data
performance_middleware = None
error_middleware = None


def get_monitoring_stats() -> Dict[str, Any]:
    """Get comprehensive monitoring statistics"""
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "monitoring_enabled": {
            "performance": ENABLE_PERFORMANCE_TRACKING,
            "tracing": ENABLE_REQUEST_TRACING,
            "detailed_logging": ENABLE_DETAILED_LOGGING
        }
    }
    
    if performance_middleware:
        stats["performance"] = performance_middleware.request_tracker.get_stats()
        stats["slow_requests"] = performance_middleware.request_tracker.get_slow_requests()
        stats["performance_alerts"] = performance_middleware.performance_alerts
    
    if error_middleware:
        stats["errors"] = error_middleware.get_error_stats()
    
    return stats


# Export main components
__all__ = [
    'PerformanceMonitoringMiddleware', 'RequestTracingMiddleware',
    'ErrorHandlingMiddleware', 'SecurityHeadersMiddleware', 'CompressionMiddleware',
    'RequestTracker', 'create_monitoring_middleware_stack', 'get_monitoring_stats'
]