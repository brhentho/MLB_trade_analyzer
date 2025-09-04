"""
Comprehensive Configuration Management System
Handles environment variables, validation, and configuration loading with type safety
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union, Type, get_type_hints
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Logging levels"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    service_key: str
    anon_key: Optional[str] = None
    pool_size: int = 10
    pool_max_overflow: int = 5
    pool_timeout: int = 30
    query_timeout: int = 30
    enable_logging: bool = False
    
    def __post_init__(self):
        if not self.url or not self.service_key:
            raise ValueError("Database URL and service key are required")


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = "redis://localhost:6379"
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str
    organization: Optional[str] = None
    model_gpt4: str = "gpt-4"
    model_gpt35: str = "gpt-3.5-turbo"
    max_tokens: int = 4000
    temperature: float = 0.1
    request_timeout: int = 60
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.api_key:
            raise ValueError("OpenAI API key is required")


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    allowed_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    cors_max_age: int = 3600
    rate_limit_per_minute: int = 60
    enable_rate_limiting: bool = True
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    def __post_init__(self):
        if not self.secret_key or len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")


@dataclass
class PerformanceConfig:
    """Performance and optimization configuration"""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_performance_monitoring: bool = True
    slow_query_threshold_seconds: float = 1.0
    memory_alert_threshold_percent: int = 85
    max_cache_size: int = 1000
    connection_pool_size: int = 10
    background_task_workers: int = 4
    request_timeout_seconds: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    enable_structured_logging: bool = False
    log_directory: str = "logs"
    log_file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_file_backup_count: int = 5
    enable_performance_logging: bool = True


@dataclass
class MLBDataConfig:
    """MLB data and external API configuration"""
    statcast_enabled: bool = True
    data_update_interval_hours: int = 6
    player_cache_ttl_seconds: int = 1800  # 30 minutes
    team_cache_ttl_seconds: int = 300     # 5 minutes
    trade_analysis_timeout_seconds: int = 180  # 3 minutes
    max_concurrent_analyses: int = 10


@dataclass
class AppConfig:
    """Main application configuration"""
    # Core settings
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    app_name: str = "Baseball Trade AI"
    app_version: str = "1.2.0"
    api_prefix: str = "/api/v1"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # Component configurations
    database: Optional[DatabaseConfig] = None
    redis: Optional[RedisConfig] = None
    openai: Optional[OpenAIConfig] = None
    security: Optional[SecurityConfig] = None
    performance: Optional[PerformanceConfig] = None
    logging: Optional[LoggingConfig] = None
    mlb_data: Optional[MLBDataConfig] = None
    
    def __post_init__(self):
        # Validate required components
        if not self.database:
            raise ValueError("Database configuration is required")
        if not self.security:
            raise ValueError("Security configuration is required")


class ConfigurationLoader:
    """
    Advanced configuration loader with environment variable handling,
    validation, and type conversion
    """
    
    def __init__(self):
        self._config_cache: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._env_file_loaded = False
    
    def load_env_file(self, env_file_path: Optional[str] = None):
        """Load environment variables from .env file"""
        if self._env_file_loaded:
            return
        
        env_file = Path(env_file_path or ".env")
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        else:
            logger.warning(f"Environment file {env_file} not found")
        
        self._env_file_loaded = True
    
    def get_env_var(self, 
                   key: str, 
                   default: Any = None, 
                   var_type: Type = str,
                   required: bool = False,
                   validator: Optional[callable] = None) -> Any:
        """
        Get environment variable with type conversion and validation
        
        Args:
            key: Environment variable name
            default: Default value if not found
            var_type: Expected type for conversion
            required: Whether the variable is required
            validator: Optional validation function
        
        Returns:
            Converted and validated value
        
        Raises:
            ValueError: If required variable is missing or validation fails
        """
        value = os.getenv(key)
        
        if value is None:
            if required:
                raise ValueError(f"Required environment variable '{key}' is not set")
            return default
        
        # Type conversion
        try:
            if var_type == bool:
                converted_value = value.lower() in ('true', '1', 'yes', 'on')
            elif var_type == int:
                converted_value = int(value)
            elif var_type == float:
                converted_value = float(value)
            elif var_type == list:
                # Assume comma-separated values
                converted_value = [item.strip() for item in value.split(',') if item.strip()]
            elif var_type == dict:
                converted_value = json.loads(value)
            else:
                converted_value = var_type(value)
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Cannot convert environment variable '{key}' to {var_type.__name__}: {e}")
        
        # Validation
        if validator and not validator(converted_value):
            raise ValueError(f"Environment variable '{key}' failed validation")
        
        return converted_value
    
    def load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment"""
        return DatabaseConfig(
            url=self.get_env_var("SUPABASE_URL", required=True),
            service_key=self.get_env_var("SUPABASE_SERVICE_KEY", required=True),
            anon_key=self.get_env_var("SUPABASE_ANON_KEY"),
            pool_size=self.get_env_var("DB_POOL_SIZE", 10, int),
            pool_max_overflow=self.get_env_var("DB_POOL_MAX_OVERFLOW", 5, int),
            pool_timeout=self.get_env_var("DB_POOL_TIMEOUT", 30, int),
            query_timeout=self.get_env_var("DB_QUERY_TIMEOUT", 30, int),
            enable_logging=self.get_env_var("DB_ENABLE_LOGGING", False, bool)
        )
    
    def load_redis_config(self) -> RedisConfig:
        """Load Redis configuration from environment"""
        return RedisConfig(
            url=self.get_env_var("REDIS_URL", "redis://localhost:6379"),
            password=self.get_env_var("REDIS_PASSWORD"),
            db=self.get_env_var("REDIS_DB", 0, int),
            max_connections=self.get_env_var("REDIS_MAX_CONNECTIONS", 20, int),
            socket_timeout=self.get_env_var("REDIS_SOCKET_TIMEOUT", 5, int),
            socket_connect_timeout=self.get_env_var("REDIS_SOCKET_CONNECT_TIMEOUT", 5, int),
            retry_on_timeout=self.get_env_var("REDIS_RETRY_ON_TIMEOUT", True, bool),
            health_check_interval=self.get_env_var("REDIS_HEALTH_CHECK_INTERVAL", 30, int)
        )
    
    def load_openai_config(self) -> OpenAIConfig:
        """Load OpenAI configuration from environment"""
        return OpenAIConfig(
            api_key=self.get_env_var("OPENAI_API_KEY", required=True),
            organization=self.get_env_var("OPENAI_ORGANIZATION"),
            model_gpt4=self.get_env_var("OPENAI_MODEL_GPT4", "gpt-4"),
            model_gpt35=self.get_env_var("OPENAI_MODEL_GPT35", "gpt-3.5-turbo"),
            max_tokens=self.get_env_var("OPENAI_MAX_TOKENS", 4000, int),
            temperature=self.get_env_var("OPENAI_TEMPERATURE", 0.1, float),
            request_timeout=self.get_env_var("OPENAI_REQUEST_TIMEOUT", 60, int),
            max_retries=self.get_env_var("OPENAI_MAX_RETRIES", 3, int)
        )
    
    def load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment"""
        return SecurityConfig(
            secret_key=self.get_env_var("SECRET_KEY", required=True),
            allowed_origins=self.get_env_var("ALLOWED_ORIGINS", 
                                           ["http://localhost:3000", "https://localhost:3000"], list),
            allowed_hosts=self.get_env_var("ALLOWED_HOSTS", 
                                         ["localhost", "127.0.0.1"], list),
            cors_max_age=self.get_env_var("CORS_MAX_AGE", 3600, int),
            rate_limit_per_minute=self.get_env_var("RATE_LIMIT_PER_MINUTE", 60, int),
            enable_rate_limiting=self.get_env_var("ENABLE_RATE_LIMITING", True, bool),
            jwt_algorithm=self.get_env_var("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=self.get_env_var("JWT_EXPIRATION_HOURS", 24, int)
        )
    
    def load_performance_config(self) -> PerformanceConfig:
        """Load performance configuration from environment"""
        return PerformanceConfig(
            enable_caching=self.get_env_var("ENABLE_CACHING", True, bool),
            cache_ttl_seconds=self.get_env_var("CACHE_TTL", 300, int),
            enable_performance_monitoring=self.get_env_var("ENABLE_PERFORMANCE_MONITORING", True, bool),
            slow_query_threshold_seconds=self.get_env_var("SLOW_QUERY_THRESHOLD", 1.0, float),
            memory_alert_threshold_percent=self.get_env_var("MEMORY_ALERT_THRESHOLD", 85, int),
            max_cache_size=self.get_env_var("MAX_CACHE_SIZE", 1000, int),
            connection_pool_size=self.get_env_var("CONNECTION_POOL_SIZE", 10, int),
            background_task_workers=self.get_env_var("BACKGROUND_TASK_WORKERS", 4, int),
            request_timeout_seconds=self.get_env_var("REQUEST_TIMEOUT", 30, int)
        )
    
    def load_logging_config(self) -> LoggingConfig:
        """Load logging configuration from environment"""
        log_level_str = self.get_env_var("LOG_LEVEL", "INFO").upper()
        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            log_level = LogLevel.INFO
            logger.warning(f"Invalid log level '{log_level_str}', using INFO")
        
        return LoggingConfig(
            level=log_level,
            enable_file_logging=self.get_env_var("ENABLE_FILE_LOGGING", True, bool),
            enable_console_logging=self.get_env_var("ENABLE_CONSOLE_LOGGING", True, bool),
            enable_structured_logging=self.get_env_var("ENABLE_STRUCTURED_LOGGING", False, bool),
            log_directory=self.get_env_var("LOG_DIR", "logs"),
            log_file_max_bytes=self.get_env_var("LOG_FILE_MAX_BYTES", 10 * 1024 * 1024, int),
            log_file_backup_count=self.get_env_var("LOG_FILE_BACKUP_COUNT", 5, int),
            enable_performance_logging=self.get_env_var("ENABLE_PERFORMANCE_LOGGING", True, bool)
        )
    
    def load_mlb_data_config(self) -> MLBDataConfig:
        """Load MLB data configuration from environment"""
        return MLBDataConfig(
            statcast_enabled=self.get_env_var("STATCAST_ENABLED", True, bool),
            data_update_interval_hours=self.get_env_var("DATA_UPDATE_INTERVAL_HOURS", 6, int),
            player_cache_ttl_seconds=self.get_env_var("PLAYER_CACHE_TTL", 1800, int),
            team_cache_ttl_seconds=self.get_env_var("TEAM_CACHE_TTL", 300, int),
            trade_analysis_timeout_seconds=self.get_env_var("TRADE_ANALYSIS_TIMEOUT", 180, int),
            max_concurrent_analyses=self.get_env_var("MAX_CONCURRENT_ANALYSES", 10, int)
        )
    
    @lru_cache(maxsize=1)
    def load_config(self) -> AppConfig:
        """Load complete application configuration"""
        with self._lock:
            # Load environment file first
            self.load_env_file()
            
            # Get environment
            env_str = self.get_env_var("ENVIRONMENT", "development")
            try:
                environment = Environment(env_str)
            except ValueError:
                environment = Environment.DEVELOPMENT
                logger.warning(f"Invalid environment '{env_str}', using development")
            
            # Load all configuration components
            try:
                config = AppConfig(
                    environment=environment,
                    debug=self.get_env_var("DEBUG", False, bool),
                    app_name=self.get_env_var("APP_NAME", "Baseball Trade AI"),
                    app_version=self.get_env_var("APP_VERSION", "1.2.0"),
                    api_prefix=self.get_env_var("API_PREFIX", "/api/v1"),
                    host=self.get_env_var("API_HOST", "0.0.0.0"),
                    port=self.get_env_var("API_PORT", 8000, int),
                    workers=self.get_env_var("API_WORKERS", 1, int),
                    reload=self.get_env_var("API_RELOAD", False, bool),
                    database=self.load_database_config(),
                    redis=self.load_redis_config(),
                    security=self.load_security_config(),
                    performance=self.load_performance_config(),
                    logging=self.load_logging_config(),
                    mlb_data=self.load_mlb_data_config()
                )
                
                # Load OpenAI config if available (optional)
                try:
                    config.openai = self.load_openai_config()
                except ValueError:
                    logger.warning("OpenAI configuration not available - some features will be limited")
                    config.openai = None
                
                logger.info(f"Configuration loaded successfully for {environment.value} environment")
                return config
                
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                raise
    
    def validate_config(self, config: AppConfig) -> List[str]:
        """
        Validate configuration and return list of issues
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Environment-specific validations
        if config.environment == Environment.PRODUCTION:
            if config.debug:
                issues.append("Debug mode should be disabled in production")
            
            if config.reload:
                issues.append("Auto-reload should be disabled in production")
            
            if config.security.secret_key == "your-secret-key-change-in-production":
                issues.append("Default secret key detected in production")
            
            if "localhost" in config.security.allowed_origins:
                issues.append("Localhost should not be allowed origin in production")
        
        # Security validations
        if len(config.security.secret_key) < 32:
            issues.append("Secret key should be at least 32 characters")
        
        # Performance validations
        if config.performance.connection_pool_size > 50:
            issues.append("Connection pool size seems excessive (>50)")
        
        if config.performance.cache_ttl_seconds < 60:
            issues.append("Cache TTL seems too short (<60 seconds)")
        
        # Database validations
        if not config.database.url.startswith(('postgresql://', 'postgres://')):
            issues.append("Database URL should use PostgreSQL")
        
        return issues


# Global configuration loader
config_loader = ConfigurationLoader()


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Get the application configuration (cached)"""
    return config_loader.load_config()


def reload_config():
    """Reload configuration (clears cache)"""
    get_config.cache_clear()
    config_loader._config_cache.clear()
    logger.info("Configuration cache cleared - will reload on next access")


def validate_configuration() -> List[str]:
    """Validate current configuration and return issues"""
    config = get_config()
    return config_loader.validate_config(config)


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_config().database


def get_redis_config() -> RedisConfig:
    """Get Redis configuration"""
    return get_config().redis


def get_openai_config() -> Optional[OpenAIConfig]:
    """Get OpenAI configuration"""
    return get_config().openai


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return get_config().security


def get_performance_config() -> PerformanceConfig:
    """Get performance configuration"""
    return get_config().performance


def get_logging_config() -> LoggingConfig:
    """Get logging configuration"""
    return get_config().logging


def get_mlb_data_config() -> MLBDataConfig:
    """Get MLB data configuration"""
    return get_config().mlb_data