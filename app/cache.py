""" In-Memory Cache for Weather Data """
import time
from typing import Dict, Any, Optional
import asyncio
from dataclasses import dataclass

@dataclass
class CacheEntry:
    data: Dict[str, Any]
    expires_at: float

class SimpleWeatherCache:
    def __init__(self, ttl_seconds: int = 900):  # 15 minutes default
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = ttl_seconds
        
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
    
# unique global cache instance
weather_cache = SimpleWeatherCache()
