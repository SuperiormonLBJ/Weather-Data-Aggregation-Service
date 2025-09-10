"""
Simple Token Bucket Rate Limiter Module

This module provides a simple token bucket rate limiting for the HTTP requests.

Why token bucket rate limiting?
    - Simple implementation
    - robust performance and allow short term spikes
    - No additional dependencies
    - Suitable for small-scale application
    - Suitable for development and testing

Author: Li Beiji
Version: 1.0.0
"""

import time
import asyncio
from ..config import RATE_LIMITS
from ..core.logger import get_logger

logger = get_logger(__name__)

class SimpleTokenBucket:
    """Simplified token bucket - just the essentials"""
    
    def __init__(self, provider: str):
        config = RATE_LIMITS.get(provider, {"tokens": 60, "refill_per_sec": 1.0})
        self.max_tokens = config["tokens"]
        self.refill_rate = config["refill_per_sec"]
        self.tokens = float(self.max_tokens)
        self.last_refill = time.time()
        self.provider = provider
        
        logger.debug(f"Token bucket created for {provider}: {self.max_tokens} tokens, {self.refill_rate}/sec refill")
    
    def _refill(self):
        """Add tokens based on time passed"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    async def wait_for_token(self):
        """Wait until we have at least 1 token"""
        wait_started = False
        start_time = time.time()
        
        while True:
            self._refill()
            if self.tokens >= 1.0:
                self.tokens -= 1.0  # Consume token
                
                if wait_started:
                    wait_time = time.time() - start_time
                    logger.info(f"{self.provider} rate limit wait completed: {wait_time:.2f}s")
                
                logger.debug(f"{self.provider} token consumed, {self.tokens:.1f} remaining")
                return
            
            if not wait_started:
                logger.warning(f"{self.provider} rate limited - waiting for tokens (have {self.tokens:.1f})")
                wait_started = True
            
            # Wait for next token
            wait_time = 1.0 / self.refill_rate
            await asyncio.sleep(wait_time)

