"""
Custom exceptions and error handling for Baseball Trade AI
Provides standardized error responses and logging
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime
from typing import Union, Dict, Any

logger = logging.getLogger(__name__)

# Custom Exception Classes
class BaseTradeAIException(Exception):
    """Base exception for all Trade AI related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class TeamNotFoundError(BaseTradeAIException):
    """Raised when a team is not found"""
    pass

class AnalysisNotFoundError(BaseTradeAIException):
    """Raised when an analysis is not found"""
    pass

class InvalidAnalysisStatusError(BaseTradeAIException):
    """Raised when analysis is in invalid status for operation"""
    pass

class DatabaseConnectionError(BaseTradeAIException):
    """Raised when database operations fail"""
    pass

class CrewAIError(BaseTradeAIException):
    """Raised when CrewAI operations fail"""
    pass

class RateLimitExceededError(BaseTradeAIException):
    """Raised when rate limits are exceeded"""
    pass

class ExternalAPIError(BaseTradeAIException):
    """Raised when external API calls fail"""
    pass

class ConfigurationError(BaseTradeAIException):
    """Raised when configuration is invalid"""
    pass

class ValidationError(BaseTradeAIException):
    """Raised when data validation fails"""
    pass

# Error Response Formatter
def create_error_response(
    status_code: int,
    message: str,
    detail: str = None,
    request_id: str = None,
    path: str = None,
    additional_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    
    response = {
        "error": message,
        "detail": detail or message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if path:
        response["path"] = path
    
    if additional_data:
        response.update(additional_data)
    
    return response

# Exception Handlers
async def base_exception_handler(request: Request, exc: BaseTradeAIException):
    """Handler for all custom Trade AI exceptions"""
    
    request_id = getattr(request.state, 'request_id', None)
    path = request.url.path
    
    # Map exception types to status codes
    status_code_map = {
        TeamNotFoundError: status.HTTP_404_NOT_FOUND,
        AnalysisNotFoundError: status.HTTP_404_NOT_FOUND,
        InvalidAnalysisStatusError: status.HTTP_409_CONFLICT,
        DatabaseConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
        CrewAIError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
        ExternalAPIError: status.HTTP_502_BAD_GATEWAY,
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ValidationError: status.HTTP_400_BAD_REQUEST,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log the error
    logger.error(
        f"Trade AI Error: {type(exc).__name__} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": path,
            "details": exc.details,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    response_data = create_error_response(
        status_code=status_code,
        message=exc.message,
        detail=str(exc.details) if exc.details else None,
        request_id=request_id,
        path=path
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for Pydantic validation errors"""
    
    request_id = getattr(request.state, 'request_id', None)
    path = request.url.path
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error on {path}",
        extra={
            "request_id": request_id,
            "errors": errors,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    response_data = create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        detail="One or more fields failed validation",
        request_id=request_id,
        path=path,
        additional_data={"validation_errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler for general HTTP exceptions"""
    
    request_id = getattr(request.state, 'request_id', None)
    path = request.url.path
    
    logger.warning(
        f"HTTP {exc.status_code} error on {path}: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    response_data = create_error_response(
        status_code=exc.status_code,
        message=exc.detail,
        request_id=request_id,
        path=path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handler for all unhandled exceptions"""
    
    request_id = getattr(request.state, 'request_id', None)
    path = request.url.path
    
    # Log the full traceback for debugging
    logger.error(
        f"Unhandled exception on {path}: {str(exc)}",
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc(),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Don't expose internal error details in production
    response_data = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal server error",
        detail="An unexpected error occurred. Please try again later.",
        request_id=request_id,
        path=path
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )

# Utility functions for raising common errors
def raise_team_not_found(team_key: str) -> None:
    """Raise team not found error with details"""
    raise TeamNotFoundError(
        f"Team '{team_key}' not found",
        details={"team_key": team_key, "suggestion": "Check available teams at /api/teams"}
    )

def raise_analysis_not_found(analysis_id: str) -> None:
    """Raise analysis not found error with details"""
    raise AnalysisNotFoundError(
        f"Analysis '{analysis_id}' not found",
        details={"analysis_id": analysis_id}
    )

def raise_invalid_analysis_status(analysis_id: str, current_status: str, expected_status: str) -> None:
    """Raise invalid analysis status error"""
    raise InvalidAnalysisStatusError(
        f"Analysis '{analysis_id}' is in status '{current_status}', expected '{expected_status}'",
        details={
            "analysis_id": analysis_id,
            "current_status": current_status,
            "expected_status": expected_status
        }
    )

def raise_database_error(operation: str, details: str = None) -> None:
    """Raise database connection error"""
    raise DatabaseConnectionError(
        f"Database operation failed: {operation}",
        details={"operation": operation, "details": details}
    )

def raise_crew_ai_error(operation: str, error_details: str = None) -> None:
    """Raise CrewAI operation error"""
    raise CrewAIError(
        f"AI analysis failed: {operation}",
        details={"operation": operation, "error_details": error_details}
    )

def raise_rate_limit_error(limit: int, window: int, retry_after: int = None) -> None:
    """Raise rate limit exceeded error"""
    raise RateLimitExceededError(
        f"Rate limit exceeded: {limit} requests per {window} seconds",
        details={
            "limit": limit,
            "window_seconds": window,
            "retry_after_seconds": retry_after
        }
    )

def raise_external_api_error(api_name: str, status_code: int = None, details: str = None) -> None:
    """Raise external API error"""
    raise ExternalAPIError(
        f"External API '{api_name}' request failed",
        details={
            "api_name": api_name,
            "status_code": status_code,
            "details": details
        }
    )

def raise_configuration_error(setting: str, details: str = None) -> None:
    """Raise configuration error"""
    raise ConfigurationError(
        f"Configuration error: {setting}",
        details={"setting": setting, "details": details}
    )

def raise_validation_error(field: str, value: Any, reason: str) -> None:
    """Raise validation error"""
    raise ValidationError(
        f"Validation failed for field '{field}': {reason}",
        details={"field": field, "value": str(value), "reason": reason}
    )