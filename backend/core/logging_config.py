"""
Structured Logging and Error Handling System
Provides comprehensive logging, error tracking, and debugging capabilities
"""

import logging
import logging.handlers
import sys
import traceback
import functools
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Callable, Union
from pathlib import Path
import os
from contextlib import contextmanager
from enum import Enum
import threading
from collections import deque

# Custom log levels
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


class LogLevel(Enum):
    """Enhanced log levels"""
    TRACE = TRACE_LEVEL
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for consistent log output
    """
    
    def __init__(self, include_extra_fields: bool = True):
        super().__init__()
        self.include_extra_fields = include_extra_fields
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if enabled
        if self.include_extra_fields:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                    'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                    'thread', 'threadName', 'processName', 'process', 'getMessage'
                }:
                    try:
                        # Ensure value is JSON serializable
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development
    """
    
    COLORS = {
        'TRACE': '\033[90m',      # Gray
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Format message with color
        message = f"{color}[{timestamp}] {record.levelname:8} {record.name:20} | {record.getMessage()}{reset}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


class LoggingManager:
    """
    Central logging configuration and management
    """
    
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: Dict[str, logging.Handler] = {}
        self.log_dir = Path(os.getenv('LOG_DIR', 'logs'))
        self.log_level = self._get_log_level()
        self.enable_file_logging = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
        self.enable_console_logging = os.getenv('ENABLE_CONSOLE_LOGGING', 'true').lower() == 'true'
        self.enable_structured_logging = os.getenv('ENABLE_STRUCTURED_LOGGING', 'false').lower() == 'true'
        
        # Create log directory
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup root logger
        self.setup_root_logger()
    
    def _get_log_level(self) -> int:
        """Get log level from environment"""
        level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        return getattr(logging, level_str, logging.INFO)
    
    def setup_root_logger(self):
        """Setup root logger with handlers"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add console handler
        if self.enable_console_logging:
            console_handler = self.get_console_handler()
            root_logger.addHandler(console_handler)
        
        # Add file handlers
        if self.enable_file_logging:
            # Main log file
            file_handler = self.get_file_handler('app.log')
            root_logger.addHandler(file_handler)
            
            # Error log file
            error_handler = self.get_error_handler('error.log')
            root_logger.addHandler(error_handler)
    
    def get_console_handler(self) -> logging.StreamHandler:
        """Get console handler"""
        handler = logging.StreamHandler(sys.stdout)
        
        if self.enable_structured_logging:
            formatter = StructuredFormatter()
        else:
            formatter = ColoredConsoleFormatter()
        
        handler.setFormatter(formatter)
        handler.setLevel(self.log_level)
        
        self.handlers['console'] = handler
        return handler
    
    def get_file_handler(self, filename: str) -> logging.Handler:
        """Get rotating file handler"""
        filepath = self.log_dir / filename
        
        handler = logging.handlers.RotatingFileHandler(
            filepath,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        formatter = StructuredFormatter() if self.enable_structured_logging else logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        handler.setFormatter(formatter)
        handler.setLevel(self.log_level)
        
        self.handlers[f'file_{filename}'] = handler
        return handler
    
    def get_error_handler(self, filename: str) -> logging.Handler:
        """Get error-specific handler"""
        filepath = self.log_dir / filename
        
        handler = logging.handlers.RotatingFileHandler(
            filepath,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)
        
        self.handlers[f'error_{filename}'] = handler
        return handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with proper configuration"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        
        # Add trace method
        def trace(message, *args, **kwargs):
            logger.log(TRACE_LEVEL, message, *args, **kwargs)
        
        logger.trace = trace
        
        self.loggers[name] = logger
        return logger


class ErrorTracker:
    """
    Error tracking and metrics collection
    """
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors: deque = deque(maxlen=max_errors)
        self.error_counts: Dict[str, int] = {}
        self.lock = threading.Lock()
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Track an error occurrence"""
        with self.lock:
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'type': type(error).__name__,
                'message': str(error),
                'context': context or {},
                'traceback': traceback.format_exc() if sys.exc_info()[0] else None
            }
            
            self.errors.append(error_info)
            
            # Update counts
            error_key = f"{type(error).__name__}: {str(error)[:100]}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        with self.lock:
            return {
                'total_errors': len(self.errors),
                'recent_errors': list(self.errors)[-10:] if self.errors else [],
                'error_counts': dict(sorted(self.error_counts.items(), 
                                          key=lambda x: x[1], reverse=True)[:10]),
                'summary_timestamp': datetime.now().isoformat()
            }


class PerformanceLogger:
    """
    Performance logging and timing utilities
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timings: Dict[str, deque] = {}
        self.lock = threading.Lock()
    
    @contextmanager
    def time_operation(self, operation_name: str, log_level: int = logging.INFO):
        """Context manager for timing operations"""
        start_time = time.time()
        self.logger.log(log_level, f"Starting operation: {operation_name}")
        
        try:
            yield
            duration = time.time() - start_time
            self.logger.log(log_level, f"Completed operation: {operation_name} in {duration:.3f}s",
                          extra={'operation': operation_name, 'duration': duration, 'status': 'success'})
            
            # Track timing
            with self.lock:
                if operation_name not in self.timings:
                    self.timings[operation_name] = deque(maxlen=100)
                self.timings[operation_name].append(duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Failed operation: {operation_name} after {duration:.3f}s - {e}",
                            extra={'operation': operation_name, 'duration': duration, 'status': 'error'},
                            exc_info=True)
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            stats = {}
            for operation, timings in self.timings.items():
                if timings:
                    stats[operation] = {
                        'count': len(timings),
                        'avg_duration': sum(timings) / len(timings),
                        'min_duration': min(timings),
                        'max_duration': max(timings),
                        'recent_duration': timings[-1] if timings else 0
                    }
            return stats


def log_exceptions(logger: logging.Logger):
    """
    Decorator to automatically log exceptions
    
    Args:
        logger: Logger to use for exception logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {e}", 
                           extra={'function': func.__name__, 'args': str(args)[:200], 'kwargs': str(kwargs)[:200]},
                           exc_info=True)
                error_tracker.track_error(e, {'function': func.__name__, 'args': args, 'kwargs': kwargs})
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {e}",
                           extra={'function': func.__name__, 'args': str(args)[:200], 'kwargs': str(kwargs)[:200]},
                           exc_info=True)
                error_tracker.track_error(e, {'function': func.__name__, 'args': args, 'kwargs': kwargs})
                raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_function_calls(logger: logging.Logger, log_level: int = logging.DEBUG):
    """
    Decorator to log function calls with parameters and results
    
    Args:
        logger: Logger to use
        log_level: Log level for the calls
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger.log(log_level, f"Calling {func.__name__}",
                      extra={'function': func.__name__, 'args': str(args)[:100], 'kwargs': str(kwargs)[:100]})
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log(log_level, f"Completed {func.__name__} in {duration:.3f}s",
                          extra={'function': func.__name__, 'duration': duration, 'status': 'success'})
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log(log_level, f"Failed {func.__name__} after {duration:.3f}s: {e}",
                          extra={'function': func.__name__, 'duration': duration, 'status': 'error'})
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger.log(log_level, f"Calling async {func.__name__}",
                      extra={'function': func.__name__, 'args': str(args)[:100], 'kwargs': str(kwargs)[:100]})
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log(log_level, f"Completed async {func.__name__} in {duration:.3f}s",
                          extra={'function': func.__name__, 'duration': duration, 'status': 'success'})
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log(log_level, f"Failed async {func.__name__} after {duration:.3f}s: {e}",
                          extra={'function': func.__name__, 'duration': duration, 'status': 'error'})
                raise
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global instances
logging_manager = LoggingManager()
error_tracker = ErrorTracker()


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger"""
    return logging_manager.get_logger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger"""
    logger = get_logger(name)
    return PerformanceLogger(logger)


def setup_logging():
    """Setup logging for the application"""
    logging_manager.setup_root_logger()
    
    # Configure specific loggers
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Baseball Trade AI specific loggers
    for module in ['agents', 'services', 'tools', 'crews', 'api']:
        logger = get_logger(f'baseball_trade_ai.{module}')
        logger.setLevel(logging_manager.log_level)
    
    return logging_manager


# Context manager for logging context
@contextmanager
def logging_context(**context):
    """Add context to all log messages in the block"""
    logger = get_logger('context')
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        for key, value in context.items():
            setattr(record, key, value)
        return record
    
    logging.setLogRecordFactory(record_factory)
    try:
        yield logger
    finally:
        logging.setLogRecordFactory(old_factory)