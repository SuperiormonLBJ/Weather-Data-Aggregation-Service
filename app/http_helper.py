"""
Simple HTTP helper with basic token bucket rate limiting
"""
import random
import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional

# Import configurations from config module
from app.config import TIMEOUTS, RATE_LIMITS, RETRY_CONFIG


class SimpleTokenBucket:
    """Simplified token bucket - just the essentials"""
    
    def __init__(self, provider: str):
        config = RATE_LIMITS.get(provider, {"tokens": 60, "refill_per_sec": 1.0})
        self.max_tokens = config["tokens"]
        self.refill_rate = config["refill_per_sec"]
        self.tokens = float(self.max_tokens)
        self.last_refill = time.time()
    
    def _refill(self):
        """Add tokens based on time passed"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    async def wait_for_token(self):
        """Wait until we have at least 1 token"""
        while True:
            self._refill()
            if self.tokens >= 1.0:
                self.tokens -= 1.0  # Consume token
                return
            
            # Wait for next token
            wait_time = 1.0 / self.refill_rate
            await asyncio.sleep(wait_time)


# Global token buckets for each provider
_buckets = {}

def get_bucket(provider: str) -> SimpleTokenBucket:
    """Get or create token bucket for provider"""
    if provider not in _buckets:
        _buckets[provider] = SimpleTokenBucket(provider)
    return _buckets[provider]


def calculate_retry_delay(attempt: int) -> float:
    """Calculate delay using exponential backoff with jitter"""
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
    
    for attempt in range(max_retries + 1):
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
                
                # Rate limited - give token back, can be cases that the rate limit is not covering all required rules
                elif response.status == 429:
                    bucket.tokens = min(bucket.max_tokens, bucket.tokens + 1)
                    last_error = f"Rate limited (HTTP 429)"
                    continue
                
                elif 500 <= response.status < 600:
                    last_error = f"Server error (HTTP {response.status})"
                    continue
                # Client errors - don't retry
                elif 400 <= response.status < 500:
                    last_error = f"Client error (HTTP {response.status})"
                    return {"provider": provider_name, "status": f"failure - {last_error}", "response_time_ms": elapsed}
                
                else:
                    last_error = f"Unexpected status (HTTP {response.status})"
                    continue

        except asyncio.TimeoutError as e:
            last_error = f"Request timeout after {TIMEOUTS[timeout_key].total}s"
            if attempt == max_retries:
                break
            continue
            
        except aiohttp.ClientError as e:
            last_error = f"Network error: {type(e).__name__} - {str(e)}"
            if attempt == max_retries:
                break
            continue
            
        except Exception as e:
            # Give token back on unexpected provider error
            bucket.tokens = min(bucket.max_tokens, bucket.tokens + 1)
            last_error = f"Unexpected error: {type(e).__name__} - {str(e)}"
            return {
                "provider": provider_name, 
                "status": "failure", 
                "error": last_error,
                "response_time_ms": total_elapsed
            }
    
    # All retries failed
    total_elapsed = round((time.perf_counter() - total_start) * 1000, 0)
    last_error = f"Failed after {max_retries + 1} attempts: {last_error}"
    
    return {"provider": provider_name, "status": f"failure - {last_error}", "response_time_ms": total_elapsed}


def get_weather_description(mapping: Dict, code: int, fallback: str) -> str:
    """Get weather description from mapping with fallback"""
    try:
        return mapping[code].value
    except KeyError:
        return fallback