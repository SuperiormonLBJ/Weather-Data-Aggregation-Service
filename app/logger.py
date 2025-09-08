"""
Logging setup for Weather Service
"""
import logging
import logging.handlers
import os
from functools import wraps
import time


def setup_logging():
    """Setup basic logging configuration"""
    
    # Get config from environment or use defaults
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/weather.log')
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Basic logging config
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s | %(levelname)-5s | %(name)s | %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            # Console output
            logging.StreamHandler(),
            # File output with rotation
            logging.handlers.RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=3
            )
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def get_logger(name: str):
    """Get logger for module"""
    return logging.getLogger(name)


def log_time(func):
    """Simple decorator to log execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            logger.info(f"{func.__name__} took {duration:.0f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.0f}ms: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            logger.info(f"{func.__name__} took {duration:.0f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.0f}ms: {e}")
            raise
    
    # Return appropriate wrapper
    if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
        return async_wrapper
    else:
        return sync_wrapper 