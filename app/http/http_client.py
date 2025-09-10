"""
Global HTTP session with connection pooling

This module provides a global consistentHTTP session with connection pooling.
So connection can be reused across requests.

Author: Li Beiji
Version: 1.0.0
"""
import aiohttp
from typing import Optional
from ..config import CONNECTION_KEEPALIVE_TIMEOUT, CONNECTION_POOL_SIZE, CONNECTION_POOL_PER_HOST
from ..core.logger import get_logger

logger = get_logger(__name__)

# Global session variable
_global_session: Optional[aiohttp.ClientSession] = None

async def get_global_session() -> aiohttp.ClientSession:
    """Get or create the global session with connection pooling"""
    global _global_session
    
    if _global_session is None or _global_session.closed:
        # Create connector with connection pooling
        connector = aiohttp.TCPConnector(
            limit=CONNECTION_POOL_SIZE,
            limit_per_host=CONNECTION_POOL_PER_HOST,
            keepalive_timeout=CONNECTION_KEEPALIVE_TIMEOUT, # 30 seconds for each connection
            enable_cleanup_closed=True
        )
        
        _global_session = aiohttp.ClientSession(connector=connector)
        logger.info(f"Created global session with connection pool: {CONNECTION_POOL_SIZE} total, {CONNECTION_POOL_PER_HOST} per host")
    
    return _global_session

async def close_global_session():
    """Close the global session"""
    global _global_session
    
    if _global_session and not _global_session.closed:
        await _global_session.close()
        logger.info("Global session closed")
        _global_session = None
