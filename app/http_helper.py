"""
Simple HTTP helper to reduce duplication in service methods
"""
import aiohttp
import time
from typing import Dict, Any, Optional

# Timeout configurations
TIMEOUTS = {
    "openweather": aiohttp.ClientTimeout(total=7, connect=2),   
    "weatherapi": aiohttp.ClientTimeout(total=7, connect=2),
    "openmeteo": aiohttp.ClientTimeout(total=8, connect=2)
}


async def make_api_request(session: aiohttp.ClientSession, url: str, params: Dict[str, Any], 
                          timeout_key: str, provider_name: str) -> Dict[str, Any]:
    """
    Generic method to make API requests with timing and error handling
    Returns: {"success": bool, "data": dict, "elapsed_ms": int} or raises Exception
    """
    start = time.perf_counter()
    try:
        async with session.get(url, params=params, timeout=TIMEOUTS[timeout_key]) as response:
            elapsed = round((time.perf_counter() - start) * 1000, 0)
            
            if response.status == 200:
                data = await response.json()
                return {"success": True, "data": data, "elapsed_ms": elapsed}
            else:
                return {"success": False, "status_code": response.status, "elapsed_ms": elapsed}
                
    except Exception as e:
        raise Exception(f"{provider_name} error: {str(e)}")


def get_weather_description(mapping: Dict, code: int, fallback: str) -> str:
    """Get weather description from mapping with fallback"""
    try:
        return mapping[code].value
    except KeyError:
        return fallback 