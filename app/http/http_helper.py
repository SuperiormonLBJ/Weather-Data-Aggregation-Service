"""
Simple HTTP helper with basic token bucket rate limiting

The module is used to standardize API requests to the weather providers, 
Inside it provides a simple HTTP helper with basic token bucket rate limiting, retry policy and timeout handling.

Author: Li Beiji
Version: 1.0.0
"""
import random
import aiohttp
import asyncio
import time
import logging
from typing import Dict, Any, Optional

# Import configurations from config module
from ..config import TIMEOUTS, RATE_LIMITS, RETRY_CONFIG
from ..core.rate_limiter import SimpleTokenBucket

# Setup logger for this module
logger = logging.getLogger(__name__)

# Global token buckets for each provider
_buckets = {}

def get_bucket(provider: str) -> SimpleTokenBucket:
    """Get or create token bucket for provider"""
    if provider not in _buckets:
        _buckets[provider] = SimpleTokenBucket(provider)
        logger.debug(f"Created new token bucket for {provider}")
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
    Make API request with simple token bucket rate limiting, retry and timeout handling.

    Args:
        session: aiohttp.ClientSession
        url: str
        params: Dict[str, Any]
        timeout_key: str
        provider_name: str
        
    Returns:
        Dict[str, Any]
        
    Raises:
        asyncio.TimeoutError
        aiohttp.ClientError
        Exception
        
    Note:
        - Rate limiting is handled by the token bucket
        - Retry policy is handled by the retry delay
        - Timeout handling is handled by the timeout config
    """
    logger.info(f"🌐 {provider_name} API request started")
    logger.debug(f"{provider_name} URL: {url}")
    logger.debug(f"{provider_name} params: {list(params.keys())}")  # Log param keys, not values (security)
    
    bucket = get_bucket(timeout_key)
    
    # Wait for token (rate limiting)
    logger.debug(f"{provider_name} waiting for rate limit token...")
    await bucket.wait_for_token()
    total_start = time.perf_counter()
    last_error = "Unknown error"
    max_retries = RETRY_CONFIG["max_retries"]
    
    logger.debug(f"{provider_name} starting request with max {max_retries} retries")
    
    for attempt in range(max_retries + 1):
        attempt_num = attempt + 1
        logger.debug(f"{provider_name} attempt {attempt_num}/{max_retries + 1}")
        
        try:
            # Wait for retry delay if not first attempt
            if attempt > 0:
                delay = calculate_retry_delay(attempt - 1)
                logger.info(f"⏱️ {provider_name} retry #{attempt} after {delay:.2f}s delay")
                await asyncio.sleep(delay)

            start = time.perf_counter()
            timeout_config = TIMEOUTS[timeout_key]
            logger.debug(f"{provider_name} timeout config: {timeout_config.total}s total, {timeout_config.connect}s connect")
            
            async with session.get(url, params=params, timeout=timeout_config) as response:
                elapsed = round((time.perf_counter() - start) * 1000, 0)
                
                logger.debug(f"{provider_name} HTTP {response.status} in {elapsed}ms")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        total_elapsed = round((time.perf_counter() - total_start) * 1000, 0)
                        
                        logger.info(f"✅ {provider_name} success in {total_elapsed}ms (attempt {attempt_num})")
                        
                        return {
                            "provider": provider_name, 
                            "status": "success", 
                            "response_time_ms": elapsed,
                            "data": data,
                            "attempts": attempt_num
                        }
                    except Exception as json_error:
                        logger.error(f"{provider_name} JSON parsing failed: {json_error}")
                        last_error = f"Invalid JSON response: {str(json_error)}"
                        continue
                
                # Rate limited - give token back
                elif response.status == 429:
                    bucket.tokens = min(bucket.max_tokens, bucket.tokens + 1)
                    last_error = f"Rate limited (HTTP 429)"
                    
                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        logger.warning(f"🚫 {provider_name} rate limited - retry after {retry_after}s")
                    else:
                        logger.warning(f"🚫 {provider_name} rate limited (attempt {attempt_num})")
                    
                    continue
                
                # Server errors - retry
                elif 500 <= response.status < 600:
                    last_error = f"Server error (HTTP {response.status})"
                    logger.warning(f"🔥 {provider_name} server error {response.status} (attempt {attempt_num})")
                    continue
                    
                # Client errors - don't retry
                elif 400 <= response.status < 500:
                    last_error = f"Client error (HTTP {response.status})"
                    total_elapsed = round((time.perf_counter() - total_start) * 1000, 0)
                    
                    logger.error(f"❌ {provider_name} client error {response.status} - not retrying")
                    
                    return {
                        "provider": provider_name, 
                        "status": f"failure - {last_error}", 
                        "response_time_ms": total_elapsed,
                        "attempts": attempt_num,
                        "data": None,
                        "error": last_error
                    }
                
                # Other status codes
                else:
                    last_error = f"Unexpected status (HTTP {response.status})"
                    logger.warning(f"⚠️ {provider_name} unexpected status {response.status} (attempt {attempt_num})")
                    continue

        except asyncio.TimeoutError:
            timeout_duration = TIMEOUTS[timeout_key].total
            last_error = f"Request timeout after {timeout_duration}s"
            
            if attempt == max_retries:
                logger.error(f"⏰ {provider_name} final timeout after {timeout_duration}s (attempt {attempt_num})")
                break
            else:
                logger.warning(f"⏰ {provider_name} timeout after {timeout_duration}s (attempt {attempt_num}) - retrying")
                continue
            
        except aiohttp.ClientError as e:
            error_type = type(e).__name__
            last_error = f"Network error: {error_type} - {str(e)}"
            
            if attempt == max_retries:
                logger.error(f"🌐 {provider_name} final network error: {error_type} (attempt {attempt_num})")
                break
            else:
                logger.warning(f"🌐 {provider_name} network error: {error_type} (attempt {attempt_num}) - retrying")
                continue
            
        except Exception as e:
            error_type = type(e).__name__
            last_error = f"Unexpected error: {error_type} - {str(e)}"
            
            logger.error(f"💥 {provider_name} unexpected error: {error_type} - {str(e)}")
            
            # Give token back for unexpected errors
            bucket.tokens = min(bucket.max_tokens, bucket.tokens + 1)
            total_elapsed = round((time.perf_counter() - total_start) * 1000, 0)
            
            return {
                "provider": provider_name, 
                "status": f"failure - {last_error}", 
                "response_time_ms": total_elapsed,
                "attempts": attempt_num,
                "data": None,
                "error": last_error
            }
    
    # All retries failed
    total_elapsed = round((time.perf_counter() - total_start) * 1000, 0)
    final_error = f"Failed after {max_retries + 1} attempts: {last_error}"
    
    logger.error(f"❌ {provider_name} all retries exhausted: {final_error} (total: {total_elapsed}ms)")
    
    return {
        "provider": provider_name, 
        "status": f"failure - {final_error}", 
        "response_time_ms": total_elapsed,
        "attempts": max_retries + 1,
        "error": final_error
    }


def get_weather_description(mapping: Dict, code: int, fallback: str) -> str:
    """
    Get weather description from standard mapping with fallback
    
    Args:
        mapping: Dict
        code: int
        fallback: str

    Returns:
        str
        
    Raises:
        KeyError
        
    Note:
        - Mapping is used to map weather codes to descriptions
        - Fallback is used when the code is not found in the mapping
    """
    try:
        description = mapping[code].value
        logger.debug(f"Weather code {code} mapped to: {description}")
        return description
    except KeyError:
        logger.debug(f"Weather code {code} not found in mapping, using fallback: {fallback}")
        return fallback