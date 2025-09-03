"""
Logging configuration for the Trading Analysis Platform
Structured logging with request tracing
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any

from .config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields from record
        extra_fields = [
            'request_id', 'user_id', 'symbol', 'analysis_type',
            'processing_time', 'cache_hit', 'error_code'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add stack trace for errors
        if record.levelno >= logging.ERROR and record.stack_info:
            log_entry["stack_trace"] = self.formatStack(record.stack_info)
        
        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Enhanced text formatter with colors and request IDs"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and request tracking"""
        
        # Add color to level name
        if sys.stdout.isatty():  # Only add colors in terminal
            level_color = self.COLORS.get(record.levelname, '')
            reset_color = self.COLORS['RESET']
            colored_level = f"{level_color}{record.levelname}{reset_color}"
        else:
            colored_level = record.levelname
        
        # Build formatted message
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Base format
        log_parts = [
            f"[{timestamp}]",
            f"[{colored_level}]",
            f"[{record.name}]",
        ]
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_parts.append(f"[REQ:{record.request_id[:8]}]")
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_parts.append(f"[USER:{record.user_id}]")
        
        # Add symbol if available
        if hasattr(record, 'symbol'):
            log_parts.append(f"[{record.symbol}]")
        
        log_parts.append(record.getMessage())
        
        formatted_message = " ".join(log_parts)
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += "\n" + self.formatException(record.exc_info)
        
        return formatted_message


def setup_logging():
    """Setup logging configuration based on environment"""
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Choose formatter based on settings
    if settings.LOG_FORMAT.lower() == 'json':
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Setup handlers
    handlers = []
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # File handler (if specified)
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(message)s'  # Formatter handles the actual formatting
    )
    
    # Configure third-party loggers
    configure_third_party_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"🔧 Logging configured",
        extra={
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
            "log_file": settings.LOG_FILE,
            "environment": settings.ENVIRONMENT
        }
    )


def configure_third_party_loggers():
    """Configure logging levels for third-party libraries"""
    
    # Reduce noise from third-party libraries in production
    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
        logging.getLogger("redis").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
    else:
        # More verbose logging in development
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message with extra context"""
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_context_logger(name: str = None, **context) -> LoggerAdapter:
    """Get a logger with predefined context"""
    logger = get_logger(name)
    return LoggerAdapter(logger, context)