"""
Advanced Security Module for Baseball Trade AI
Production-ready JWT authentication, rate limiting, and security features
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple, Any, Union

import jwt
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from passlib.hash import bcrypt

logger = logging.getLogger(__name__)

# Security configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
JWT_REFRESH_HOURS = int(os.getenv('JWT_REFRESH_HOURS', '168'))  # 1 week

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
RATE_LIMIT_BURST = int(os.getenv('RATE_LIMIT_BURST', '20'))

# Security settings
ENABLE_2FA = os.getenv('ENABLE_2FA', 'false').lower() == 'true'
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION', '900'))  # 15 minutes
ENABLE_IP_WHITELIST = os.getenv('ENABLE_IP_WHITELIST', 'false').lower() == 'true'
ALLOWED_IPS = set(os.getenv('ALLOWED_IPS', '').split(',')) if ENABLE_IP_WHITELIST else set()

# Password requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_SPECIAL_CHARS = True
REQUIRE_NUMBERS = True
REQUIRE_UPPERCASE = True


class SecurityConfig:
    """Security configuration management"""
    
    @staticmethod
    def validate_environment():
        """Validate security configuration"""
        issues = []
        
        if JWT_SECRET_KEY == 'your-secret-key':
            issues.append("Default JWT secret key detected - change in production")
        
        if len(JWT_SECRET_KEY) < 32:
            issues.append("JWT secret key too short - use at least 32 characters")
        
        if JWT_EXPIRATION_HOURS > 168:  # 1 week
            issues.append("JWT expiration too long - consider shorter duration")
        
        if RATE_LIMIT_REQUESTS > 1000:
            issues.append("Rate limit too high - consider lower limits")
        
        return issues


class PasswordValidator:
    """Advanced password validation"""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """Validate password against security requirements"""
        errors = []
        
        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        
        if len(password) > 128:
            errors.append("Password too long (max 128 characters)")
        
        if REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letters")
        
        if REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain numbers")
        
        if REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special characters")
        
        # Check for common patterns
        if re.search(r'(.)\1{3,}', password):  # 4+ repeated chars
            errors.append("Password contains too many repeated characters")
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            errors.append("Password contains sequential numbers")
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmnop|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            errors.append("Password contains sequential letters")
        
        # Common weak passwords
        weak_passwords = {
            'password', 'password123', '123456', 'qwerty', 'admin', 
            'letmein', 'welcome', 'monkey', '1234567890'
        }
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_password_strength_score(password: str) -> int:
        """Generate password strength score (0-100)"""
        score = 0
        
        # Length bonus
        score += min(password.__len__() * 2, 20)
        
        # Character variety
        if re.search(r'[a-z]', password): score += 10
        if re.search(r'[A-Z]', password): score += 10
        if re.search(r'\d', password): score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 15
        
        # Bonus for length > 12
        if len(password) > 12: score += 10
        
        # Penalty for patterns
        if re.search(r'(.)\1{2,}', password): score -= 10
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password): score -= 15
        
        return max(0, min(100, score))


class JWTManager:
    """Advanced JWT token management"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        self.token_blacklist: Set[str] = set()  # In production, use Redis
        self.refresh_tokens: Dict[str, Dict] = {}  # In production, use database
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        user_id: str, 
        username: str,
        roles: List[str] = None,
        scopes: List[str] = None,
        additional_claims: Dict = None
    ) -> str:
        """Create JWT access token"""
        
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles or ["user"],
            "scopes": scopes or ["read", "write"],
            "iat": now.timestamp(),
            "exp": expires.timestamp(),
            "type": "access",
            "jti": hashlib.md5(f"{user_id}:{now.timestamp()}".encode()).hexdigest()
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        try:
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            logger.info(f"Created access token for user {username}")
            return token
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating access token"
            )
    
    def create_refresh_token(self, user_id: str, username: str) -> str:
        """Create JWT refresh token"""
        
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=JWT_REFRESH_HOURS)
        
        payload = {
            "sub": user_id,
            "username": username,
            "iat": now.timestamp(),
            "exp": expires.timestamp(),
            "type": "refresh",
            "jti": hashlib.md5(f"refresh:{user_id}:{now.timestamp()}".encode()).hexdigest()
        }
        
        try:
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            # Store refresh token (in production, use database)
            self.refresh_tokens[payload["jti"]] = {
                "user_id": user_id,
                "username": username,
                "created_at": now,
                "expires_at": expires
            }
            
            logger.info(f"Created refresh token for user {username}")
            return token
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating refresh token"
            )
    
    def decode_token(self, token: str) -> Dict:
        """Decode and validate JWT token"""
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti in self.token_blacklist:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token"""
        
        try:
            payload = self.decode_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            jti = payload.get("jti")
            if jti not in self.refresh_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found"
                )
            
            user_data = self.refresh_tokens[jti]
            
            # Create new access token
            return self.create_access_token(
                user_id=user_data["user_id"],
                username=user_data["username"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    def revoke_token(self, token: str) -> bool:
        """Revoke/blacklist a token"""
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            
            if jti:
                self.token_blacklist.add(jti)
                
                # If it's a refresh token, remove from store
                if payload.get("type") == "refresh" and jti in self.refresh_tokens:
                    del self.refresh_tokens[jti]
                
                logger.info(f"Revoked token {jti}")
                return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
        
        return False
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict:
        """Get current user from JWT token"""
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        payload = self.decode_token(credentials.credentials)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "scopes": payload.get("scopes", []),
            "token_jti": payload.get("jti")
        }


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        # In-memory storage (use Redis in production)
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.user_limits: Dict[str, Dict] = {}  # Custom user limits
    
    def _get_client_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """Generate client key for rate limiting"""
        client_ip = request.client.host
        
        if user_id:
            return f"user:{user_id}"
        else:
            return f"ip:{client_ip}"
    
    def _clean_old_requests(self, requests: List[float], window: int) -> List[float]:
        """Remove requests older than the window"""
        current_time = time.time()
        return [req_time for req_time in requests if current_time - req_time < window]
    
    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        endpoint_specific: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request should be rate limited"""
        
        current_time = time.time()
        client_key = self._get_client_key(request, user_id)
        
        # Use custom limits or defaults
        request_limit = limit or RATE_LIMIT_REQUESTS
        time_window = window or RATE_LIMIT_WINDOW
        
        # Check if IP is temporarily blocked
        if client_key in self.blocked_ips:
            if current_time - self.blocked_ips[client_key] < LOCKOUT_DURATION:
                return False, {
                    "error": "IP_BLOCKED",
                    "message": "IP temporarily blocked due to excessive requests",
                    "retry_after": int(LOCKOUT_DURATION - (current_time - self.blocked_ips[client_key]))
                }
            else:
                del self.blocked_ips[client_key]
        
        # Endpoint-specific key
        if endpoint_specific:
            endpoint_key = f"{client_key}:{request.method}:{request.url.path}"
        else:
            endpoint_key = client_key
        
        # Get and clean request history
        if endpoint_key not in self.requests:
            self.requests[endpoint_key] = []
        
        self.requests[endpoint_key] = self._clean_old_requests(
            self.requests[endpoint_key], time_window
        )
        
        # Check limits
        request_count = len(self.requests[endpoint_key])
        
        if request_count >= request_limit:
            # Block IP after excessive requests
            if request_count >= request_limit * 2:
                self.blocked_ips[client_key] = current_time
                logger.warning(f"Blocked IP {client_key} for excessive requests")
            
            return False, {
                "error": "RATE_LIMITED",
                "message": f"Too many requests. Limit: {request_limit}/{time_window}s",
                "requests_made": request_count,
                "limit": request_limit,
                "window": time_window,
                "retry_after": time_window
            }
        
        # Add current request
        self.requests[endpoint_key].append(current_time)
        
        return True, {
            "requests_remaining": request_limit - request_count - 1,
            "limit": request_limit,
            "window": time_window,
            "reset_time": int(current_time + time_window)
        }
    
    def set_user_limits(self, user_id: str, limits: Dict[str, int]):
        """Set custom rate limits for a user"""
        self.user_limits[user_id] = limits
        logger.info(f"Set custom rate limits for user {user_id}: {limits}")
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        current_time = time.time()
        
        return {
            "total_tracked_clients": len(self.requests),
            "blocked_ips": len(self.blocked_ips),
            "active_requests": sum(
                len(self._clean_old_requests(reqs, RATE_LIMIT_WINDOW))
                for reqs in self.requests.values()
            ),
            "custom_user_limits": len(self.user_limits)
        }


class SecurityValidator:
    """Advanced security validation and sanitization"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_safe_url(url: str) -> bool:
        """Check if URL is safe (no SSRF attacks)"""
        # Block private IP ranges
        private_ranges = [
            '10.0.0.0/8',
            '172.16.0.0/12', 
            '192.168.0.0/16',
            '127.0.0.0/8',
            '169.254.0.0/16',
            'fc00::/7',
            '::1/128'
        ]
        
        try:
            from urllib.parse import urlparse
            import ipaddress
            
            parsed = urlparse(url)
            if not parsed.hostname:
                return False
            
            # Check if hostname is an IP
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                for private_range in private_ranges:
                    if ip in ipaddress.ip_network(private_range):
                        return False
            except ValueError:
                # Not an IP, check domain
                pass
            
            # Block localhost variants
            localhost_variants = ['localhost', '0.0.0.0']
            if parsed.hostname.lower() in localhost_variants:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not isinstance(text, str):
            text = str(text)
        
        # Truncate if too long
        text = text[:max_length]
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Basic XSS prevention
        text = text.replace('<script', '&lt;script')
        text = text.replace('</script>', '&lt;/script&gt;')
        text = text.replace('javascript:', 'javascript_')
        text = text.replace('vbscript:', 'vbscript_')
        
        return text.strip()
    
    @staticmethod
    def validate_file_upload(filename: str, content: bytes, allowed_extensions: Set[str]) -> Tuple[bool, str]:
        """Validate file uploads"""
        if not filename:
            return False, "Filename required"
        
        # Check extension
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        if extension not in allowed_extensions:
            return False, f"File type not allowed. Allowed: {allowed_extensions}"
        
        # Check file size (10MB limit)
        if len(content) > 10 * 1024 * 1024:
            return False, "File too large (max 10MB)"
        
        # Basic content validation
        if extension in ['jpg', 'jpeg', 'png', 'gif']:
            # Check for image magic bytes
            image_signatures = [
                b'\xff\xd8\xff',  # JPEG
                b'\x89\x50\x4e\x47',  # PNG
                b'\x47\x49\x46\x38'   # GIF
            ]
            
            if not any(content.startswith(sig) for sig in image_signatures):
                return False, "Invalid image file"
        
        return True, "Valid file"


# Global instances
jwt_manager = JWTManager()
rate_limiter = RateLimiter()
security_validator = SecurityValidator()


# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> Dict:
    """FastAPI dependency for getting current user"""
    return await jwt_manager.get_current_user(credentials)


async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """FastAPI dependency for getting active user"""
    # In a real implementation, check user is active in database
    return current_user


async def require_roles(required_roles: List[str]):
    """Dependency factory for role-based access control"""
    
    def check_roles(current_user: Dict = Depends(get_current_user)) -> Dict:
        user_roles = current_user.get("roles", [])
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}"
            )
        
        return current_user
    
    return check_roles


async def require_scopes(required_scopes: List[str]):
    """Dependency factory for scope-based access control"""
    
    def check_scopes(current_user: Dict = Depends(get_current_user)) -> Dict:
        user_scopes = current_user.get("scopes", [])
        
        if not any(scope in user_scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scopes: {required_scopes}"
            )
        
        return current_user
    
    return check_scopes


def check_rate_limit(
    limit: Optional[int] = None,
    window: Optional[int] = None,
    endpoint_specific: bool = False
):
    """Dependency factory for rate limiting"""
    
    async def rate_limit_dependency(request: Request, current_user: Optional[Dict] = None):
        user_id = current_user.get("user_id") if current_user else None
        
        allowed, info = await rate_limiter.check_rate_limit(
            request, user_id, limit, window, endpoint_specific
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=info,
                headers={"Retry-After": str(info.get("retry_after", window or RATE_LIMIT_WINDOW))}
            )
        
        return info
    
    return rate_limit_dependency


# Export main components
__all__ = [
    'JWTManager', 'RateLimiter', 'SecurityValidator', 'PasswordValidator',
    'jwt_manager', 'rate_limiter', 'security_validator',
    'get_current_user', 'get_current_active_user', 
    'require_roles', 'require_scopes', 'check_rate_limit'
]