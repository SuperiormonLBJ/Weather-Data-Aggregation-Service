""" In-Memory Cache for Weather Data """
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..config import CACHE_TTL_SECONDS

@dataclass
class CacheEntry:
    data: Dict[str, Any]
    expires_at: float

class SimpleWeatherCache:
    def __init__(self, ttl_seconds: int = None):
        # Use config value if not specified
        self._ttl = ttl_seconds if ttl_seconds is not None else CACHE_TTL_SECONDS
        self._cache: Dict[str, CacheEntry] = {}
        
    def _cleanup_expired(self):
        """Remove expired entries"""
        now = time.time()
        expired_keys = [k for k, v in self._cache.items() if v.expires_at <= now]
        for key in expired_keys:
            del self._cache[key]
    
    def get(self, location: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data, returns None if not found or expired"""
        self._cleanup_expired()
        
        entry = self._cache.get(location.lower())
        if entry and entry.expires_at > time.time():
            return entry.data
        return None
    
    def set(self, location: str, data: Dict[str, Any]):
        """Cache weather data"""
        expires_at = time.time() + self._ttl
        self._cache[location.lower()] = CacheEntry(data, expires_at)
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()

# Global cache instance using config
weather_cache = SimpleWeatherCache()
