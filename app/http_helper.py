"""
Simple HTTP helper with basic token bucket rate limiting
"""
import random
import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional

# Timeout configurations
TIMEOUTS = {
    "openweather": aiohttp.ClientTimeout(total=7, connect=2),   
    "weatherapi": aiohttp.ClientTimeout(total=7, connect=2),
    "openmeteo": aiohttp.ClientTimeout(total=8, connect=2)
}

# Simple rate limit configs
LIMITS = {
    "openweather": {"tokens": 60, "refill_per_sec": 1.0},  # 60 tokens, refill 1/sec
    "weatherapi": {"tokens": 100, "refill_per_sec": 1.5},  # 100 tokens, refill 1.5/sec
    "openmeteo": {"tokens": 1000, "refill_per_sec": 10.0}  # 600 tokens, refill 10/sec
}

# Retry configurations
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,      # Start with 1 second delay
    "max_delay": 16.0,      # Cap max delay at 16 seconds
    "jitter_factor": 0.1,   # 10% jitter
    "backoff_multiplier": 2.0  # Double each time delay
}


class SimpleTokenBucket:
    """Simplified token bucket - just the essentials"""
    
    def __init__(self, provider: str):
        config = LIMITS.get(provider, {"tokens": 60, "refill_per_sec": 1.0})
        self.max_tokens = config["tokens"]
        self.refill_rate = config["refill_per_sec"]
        self.tokens = float(self.max_tokens)  # Start full
        self.last_update = time.time()
    
    def _refill(self):
        """Add tokens based on time passed"""
        now = time.time()
        time_passed = now - self.last_update
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_update = now
    
    def can_request(self) -> bool:
        """Check if we have tokens for a request"""
        self._refill()
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
    
    async def wait_for_token(self):
        """Wait until we have a token"""
        while not self.can_request():
            # Calculate wait time
            wait_time = 1.0 / self.refill_rate  # Time taken for refill 1 token
            await asyncio.sleep(min(wait_time, 1.0))  # Max 1 second wait


# Global buckets
_buckets = {}

def get_bucket(provider: str) -> SimpleTokenBucket:
    """Get bucket for provider"""
    if provider not in _buckets:
        _buckets[provider] = SimpleTokenBucket(provider)
    return _buckets[provider]

def calculate_retry_delay(attempt: int) -> float:
    """
    Calculate delay using exponential backoff with jitter
    
    Formula: base_delay * (backoff_multiplier ^ attempt) + jitter
    Jitter prevents thundering herd problem
    """
    base_delay = RETRY_CONFIG["base_delay"]
    multiplier = RETRY_CONFIG["backoff_multiplier"]
    max_delay = RETRY_CONFIG["max_delay"]
    jitter_factor = RETRY_CONFIG["jitter_factor"]
    
    # Exponential backoff: 1s, 2s, 4s, 8s, 16s...
    delay = base_delay * (multiplier ** attempt)
    delay = min(delay, max_delay)  # Cap at max_delay
    
    # Add jitter: ±10% randomness
    jitter = delay * jitter_factor * (random.random() * 2 - 1)
    
    return max(0.1, delay + jitter)  # Never less than 0.1 seconds


async def make_api_request(session: aiohttp.ClientSession, url: str, params: Dict[str, Any], 
                          timeout_key: str, provider_name: str) -> Dict[str, Any]:
    """
    Make API request with simple token bucket rate limiting
    """
    bucket = get_bucket(timeout_key)
    # Wait for token (rate limiting)
    await bucket.wait_for_token()
    total_start = time.perf_counter()
    last_error = "Unknown error"
    max_retries = RETRY_CONFIG["max_retries"]

    for attempt in range(max_retries):
        try:
            # Wait for delay if not first attempt
            if attempt > 0:
                delay = calculate_retry_delay(attempt - 1)
                await asyncio.sleep(delay)

            start = time.perf_counter()
            async with session.get(url, params=params, timeout=TIMEOUTS[timeout_key]) as response:
                elapsed = round((time.perf_counter() - start) * 1000, 0)
                
                if response.status == 200:
                    data = await response.json()
                    return {"provider": provider_name, "status": "success", "response_time_ms": elapsed, "data": data}
                
                elif response.status == 429:
                    # Too many request, retry after delay
                    continue

                elif 500 <= response.status < 600:
                    # Server error, retry after delay
                    continue
                
                # Client errors - don't retry
                elif 400 <= response.status < 500:
                    # last_error = f"Client error (HTTP {response.status})"
                    # logger.error(f"{provider_name} client error {response.status} - not retrying")
                    break 
                
                else:
                    return {"provider": provider_name, "status": "failure", "response_time_ms": elapsed}
                    

        except Exception as e:
            # Give token back on provider error
            bucket.tokens = min(bucket.max_tokens, bucket.tokens + 1)
            raise Exception(f"{provider_name} error: {str(e)}")
    
    # All retries failed
    total_elapsed = round((time.perf_counter() - total_start) * 1000, 0)
    last_error = f"Failed after {max_retries + 1} attempts: {last_error}"
    #logger.error(f"{provider_name} failed after {max_retries + 1} attempts: {last_error}")
    
    return {"provider": provider_name, "status": "failure", "response_time_ms": elapsed}


def get_weather_description(mapping: Dict, code: int, fallback: str) -> str:
    """Get weather description from mapping with fallback"""
    try:
        return mapping[code].value
    except KeyError:
        return fallback