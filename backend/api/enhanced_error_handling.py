"""
Enhanced error handling for production deployment
Implements secure error responses and comprehensive logging
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import os
import uuid

logger = logging.getLogger(__name__)

class ProductionErrorHandler:
    """Production-ready error handling with security considerations"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = self.environment == 'development'
    
    def create_error_response(
        self,
        status_code: int,
        error_type: str,
        message: str,
        detail: Optional[str] = None,
        request_id: Optional[str] = None,
        debug_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        
        response = {
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status_code": status_code
            }
        }
        
        if request_id:
            response["error"]["request_id"] = request_id
        
        # Include detail in development or for client errors (4xx)
        if detail and (self.debug or 400 <= status_code < 500):
            response["error"]["detail"] = detail
        
        # Include debug info only in development
        if debug_info and self.debug:
            response["error"]["debug"] = debug_info
            
        # Add support contact for production errors
        if not self.debug and status_code >= 500:
            response["error"]["support"] = {
                "message": "Please contact support if this error persists",
                "reference_id": request_id or str(uuid.uuid4())[:8]
            }
        
        return response
    
    async def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors"""
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        # Format validation errors for client
        validation_errors = []
        for error in exc.errors():
            field_path = " → ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": self._sanitize_validation_message(error["msg"]),
                "type": error["type"],
                "input": str(error.get("input", ""))[:100] if self.debug else None
            })
        
        # Log validation error
        logger.warning(
            f"Validation error on {request.url.path}",
            extra={
                "request_id": request_id,
                "validation_errors": validation_errors,
                "user_agent": request.headers.get("user-agent", "")[:200],
                "client_ip": request.client.host
            }
        )
        
        error_response = self.create_error_response(
            status_code=422,
            error_type="validation_error",
            message="Request validation failed",
            detail="One or more fields contain invalid data",
            request_id=request_id,
            debug_info={"validation_errors": validation_errors} if self.debug else None
        )
        
        if not self.debug:
            # In production, provide structured validation errors without internal details
            error_response["error"]["validation_errors"] = [
                {
                    "field": error["field"],
                    "message": error["message"]
                }
                for error in validation_errors
            ]
        
        return JSONResponse(
            status_code=422,
            content=error_response
        )
    
    async def handle_http_error(self, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        # Map status codes to user-friendly messages
        status_messages = {
            400: "Bad Request",
            401: "Authentication Required", 
            403: "Access Denied",
            404: "Resource Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        
        user_message = status_messages.get(exc.status_code, "An error occurred")
        
        # Log the error with appropriate level
        log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
        logger.log(
            log_level,
            f"HTTP {exc.status_code} error on {request.url.path}: {exc.detail}",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "user_agent": request.headers.get("user-agent", "")[:200],
                "client_ip": request.client.host
            }
        )
        
        error_response = self.create_error_response(
            status_code=exc.status_code,
            error_type="http_error",
            message=user_message,
            detail=str(exc.detail) if self.debug else None,
            request_id=request_id
        )
        
        # Add retry information for rate limiting
        headers = {}
        if exc.status_code == 429:
            headers["Retry-After"] = "60"
            error_response["error"]["retry_after"] = 60
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers=headers
        )
    
    async def handle_general_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions"""
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        # Log the full error with traceback
        logger.error(
            f"Unhandled exception on {request.url.path}: {str(exc)}",
            extra={
                "request_id": request_id,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "user_agent": request.headers.get("user-agent", "")[:200],
                "client_ip": request.client.host,
                "request_method": request.method,
                "request_path": request.url.path,
                "query_params": str(request.query_params)
            },
            exc_info=True
        )
        
        # Create safe error response for production
        if self.debug:
            message = f"Internal server error: {str(exc)}"
            detail = traceback.format_exc()
        else:
            message = "An unexpected error occurred"
            detail = "Please try again later or contact support if the problem persists"
        
        error_response = self.create_error_response(
            status_code=500,
            error_type="internal_error", 
            message=message,
            detail=detail,
            request_id=request_id,
            debug_info={"exception_type": type(exc).__name__} if self.debug else None
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    async def handle_database_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle database-related errors"""
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        logger.error(
            f"Database error on {request.url.path}: {str(exc)}",
            extra={
                "request_id": request_id,
                "database_error": str(exc),
                "user_agent": request.headers.get("user-agent", "")[:200],
                "client_ip": request.client.host
            }
        )
        
        error_response = self.create_error_response(
            status_code=503,
            error_type="service_unavailable",
            message="Database service temporarily unavailable",
            detail="Please try again in a few moments" if not self.debug else str(exc),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=503,
            content=error_response,
            headers={"Retry-After": "30"}
        )
    
    async def handle_external_api_error(self, request: Request, service_name: str, exc: Exception) -> JSONResponse:
        """Handle external API errors (OpenAI, etc.)"""
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        logger.error(
            f"External API error ({service_name}) on {request.url.path}: {str(exc)}",
            extra={
                "request_id": request_id,
                "service_name": service_name,
                "external_error": str(exc),
                "user_agent": request.headers.get("user-agent", "")[:200],
                "client_ip": request.client.host
            }
        )
        
        error_response = self.create_error_response(
            status_code=502,
            error_type="external_service_error",
            message=f"{service_name} service temporarily unavailable",
            detail="AI analysis service is experiencing issues. Please try again later.",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=502,
            content=error_response,
            headers={"Retry-After": "60"}
        )
    
    def _sanitize_validation_message(self, message: str) -> str:
        """Sanitize validation error messages to prevent information disclosure"""
        
        # Remove potentially sensitive information from validation messages
        sensitive_patterns = [
            "ensure this value has at most",  # Length constraints might reveal limits
            "ensure this value has at least", 
            "field required"  # Generic enough to keep
        ]
        
        # Keep safe, user-friendly messages
        safe_messages = {
            "field required": "This field is required",
            "value is not a valid email address": "Please enter a valid email address",
            "value is not a valid integer": "Please enter a valid number",
            "value is not a valid uuid": "Invalid ID format",
            "str type expected": "Text value expected",
            "int type expected": "Numeric value expected"
        }
        
        return safe_messages.get(message, "Invalid value")
    
    def setup_error_handlers(self, app):
        """Setup all error handlers for the FastAPI app"""
        
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return await self.handle_validation_error(request, exc)
        
        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            return await self.handle_http_error(request, exc)
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            # Check for specific error types first
            if "database" in str(exc).lower() or "supabase" in str(exc).lower():
                return await self.handle_database_error(request, exc)
            elif "openai" in str(exc).lower() or "api" in str(exc).lower():
                return await self.handle_external_api_error(request, "AI Service", exc)
            else:
                return await self.handle_general_error(request, exc)

# Create global error handler instance
error_handler = ProductionErrorHandler()

# Convenience functions for raising specific errors
class BusinessLogicError(HTTPException):
    """Custom exception for business logic errors"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(status_code=400, detail=message)
        self.business_detail = detail

class ResourceNotFoundError(HTTPException):
    """Custom exception for resource not found errors"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found"
        super().__init__(status_code=404, detail=message)
        self.resource_type = resource_type
        self.resource_id = resource_id

class RateLimitError(HTTPException):
    """Custom exception for rate limit errors"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(status_code=429, detail=message)
        self.retry_after = retry_after

class ServiceUnavailableError(HTTPException):
    """Custom exception for service unavailable errors"""
    def __init__(self, service_name: str, retry_after: int = 30):
        message = f"{service_name} is temporarily unavailable"
        super().__init__(status_code=503, detail=message)
        self.service_name = service_name
        self.retry_after = retry_after