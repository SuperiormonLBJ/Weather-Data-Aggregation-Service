""" 
Simple Weather Cache Module using cachetools

This module provides a simple but effective cache for weather data using cachetools.
It offers LRU eviction, TTL support, and basic statistics with minimal code.

Benefits of cachetools:
- Lightweight and well-maintained
- Built-in LRU eviction
- Thread-safe
- Simple API

Author: Li Beiji
Version: 2.0.1
"""
import time
from typing import Dict, Any, Optional
from cachetools import TTLCache
from ..config import CACHE_TTL_SECONDS
from ..core.logger import get_logger

logger = get_logger(__name__)

class WeatherCache:
    """Simple weather cache using cachetools TTLCache"""
    
    def __init__(self, ttl_seconds: int = None, max_size: int = 1000):
        """
        Initialize cache with TTL and size limits
        
        Args:
            ttl_seconds: Time to live for cache entries (default from config)
            max_size: Maximum number of entries before LRU eviction
        """
        # Fix: Ensure ttl_seconds is never None
        self._ttl = ttl_seconds if ttl_seconds is not None else CACHE_TTL_SECONDS
        self._max_size = max_size
        
        # Fix: Use self._ttl instead of ttl_seconds to ensure it's never None
        self._cache = TTLCache(maxsize=max_size, ttl=self._ttl)
        
        # Simple statistics
        self._hits = 0
        self._misses = 0
        
        logger.info(f"Cache initialized: TTL={self._ttl}s, Max Size={self._max_size}")
    
    def _normalize_key(self, location: str) -> str:
        """Normalize location key for consistent caching"""
        normalized = location.strip().lower()
        
        # For coordinates, normalize precision
        if ',' in normalized:
            try:
                parts = [float(p.strip()) for p in normalized.split(',')]
                if len(parts) == 2:
                    normalized = f"{parts[0]:.4f},{parts[1]:.4f}"
            except ValueError:
                pass  # Keep original if not valid coordinates
                
        return normalized
    
    def get(self, location: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data with error handling"""
        key = self._normalize_key(location)
        
        try:
            data = self._cache[key]
            self._hits += 1
            logger.debug(f"Cache hit: {key}")
            return data
        except KeyError:
            self._misses += 1
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            # Handle any comparison errors from cachetools
            logger.warning(f"Cache get error for {key}: {e}")
            self._misses += 1
            return None
    
    def set(self, location: str, data: Dict[str, Any]):
        """Cache weather data with error handling"""
        key = self._normalize_key(location)
        
        try:
            self._cache[key] = data
            logger.debug(f"Cache set: {key}")
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            # If caching fails, we can still continue without caching
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic cache statistics"""
        total_requests = self._hits + self._misses
        hit_ratio = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_ratio": round(hit_ratio, 2),
            "current_size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl
        }
    
    def clear(self):
        """Clear all cache entries"""
        size_before = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {size_before} entries removed")

# Global cache instance
weather_cache = WeatherCache()
