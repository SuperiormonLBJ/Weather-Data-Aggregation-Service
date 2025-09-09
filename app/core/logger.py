"""
Logging setup for weather service
"""
import asyncio
import logging
import logging.handlers
import os
from functools import wraps
import time
from app.config import LOG_LEVEL, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

def setup_logging():
    """Setup basic logging configuration using config values"""
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Basic logging config using config values
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Set specific loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info(f"📋 Logging configured - Level: {LOG_LEVEL}, File: {LOG_FILE}")

def get_logger(name: str = None):
    """Get logger instance"""
    return logging.getLogger(name or __name__)

def log_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            duration = round((time.perf_counter() - start) * 1000, 2)
            logger = get_logger(func.__module__)
            logger.debug(f"⏱️ {func.__name__} took {duration}ms")
            return result
        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 2)
            logger = get_logger(func.__module__)
            logger.error(f"❌ {func.__name__} failed after {duration}ms: {str(e)}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = round((time.perf_counter() - start) * 1000, 2)
            logger = get_logger(func.__module__)
            logger.debug(f"⏱️ {func.__name__} took {duration}ms")
            return result
        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 2)
            logger = get_logger(func.__module__)
            logger.error(f"❌ {func.__name__} failed after {duration}ms: {str(e)}")
            raise
    
    if asyncio and asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper 