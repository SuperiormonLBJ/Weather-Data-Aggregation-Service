"""
Configuration settings for the Weather Data Aggregation Service
"""
import os
import aiohttp
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# API CREDENTIALS
# ============================================================================

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY')

# ============================================================================
# CACHE CONFIGURATION  
# ============================================================================

CACHE_TTL_SECONDS: int = int(os.getenv('CACHE_TTL', '600'))  # 10 minutes default

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE: str = os.getenv('LOG_FILE', 'logs/weather.log')
LOG_FORMAT: str = '%(asctime)s | %(levelname)-5s | %(name)s | %(message)s'
LOG_DATE_FORMAT: str = '%H:%M:%S'

# ============================================================================
# API TIMEOUT CONFIGURATIONS
# ============================================================================

OPENWEATHER_TIMEOUT_TOTAL: float = float(os.getenv('OPENWEATHER_TIMEOUT_TOTAL', '7.0'))
OPENWEATHER_TIMEOUT_CONNECT: float = float(os.getenv('OPENWEATHER_TIMEOUT_CONNECT', '2.0'))

WEATHERAPI_TIMEOUT_TOTAL: float = float(os.getenv('WEATHERAPI_TIMEOUT_TOTAL', '7.0'))
WEATHERAPI_TIMEOUT_CONNECT: float = float(os.getenv('WEATHERAPI_TIMEOUT_CONNECT', '2.0'))

OPENMETEO_TIMEOUT_TOTAL: float = float(os.getenv('OPENMETEO_TIMEOUT_TOTAL', '8.0'))
OPENMETEO_TIMEOUT_CONNECT: float = float(os.getenv('OPENMETEO_TIMEOUT_CONNECT', '2.0'))

# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

OPENWEATHER_TOKENS: int = int(os.getenv('OPENWEATHER_TOKENS', '60'))
OPENWEATHER_REFILL_RATE: float = float(os.getenv('OPENWEATHER_REFILL_RATE', '1.0'))

WEATHERAPI_TOKENS: int = int(os.getenv('WEATHERAPI_TOKENS', '100'))
WEATHERAPI_REFILL_RATE: float = float(os.getenv('WEATHERAPI_REFILL_RATE', '1.5'))

OPENMETEO_TOKENS: int = int(os.getenv('OPENMETEO_TOKENS', '1000'))
OPENMETEO_REFILL_RATE: float = float(os.getenv('OPENMETEO_REFILL_RATE', '10.0'))

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================

MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
BASE_DELAY: float = float(os.getenv('BASE_DELAY', '1.0'))
MAX_DELAY: float = float(os.getenv('MAX_DELAY', '16.0'))
JITTER_FACTOR: float = float(os.getenv('JITTER_FACTOR', '0.1'))
BACKOFF_MULTIPLIER: float = float(os.getenv('BACKOFF_MULTIPLIER', '2.0'))

# ============================================================================
# CONSTRUCTED CONFIGURATIONS
# ============================================================================

TIMEOUTS = {
    "openweather": aiohttp.ClientTimeout(
        total=OPENWEATHER_TIMEOUT_TOTAL,
        connect=OPENWEATHER_TIMEOUT_CONNECT
    ),
    "weatherapi": aiohttp.ClientTimeout(
        total=WEATHERAPI_TIMEOUT_TOTAL,
        connect=WEATHERAPI_TIMEOUT_CONNECT
    ),
    "openmeteo": aiohttp.ClientTimeout(
        total=OPENMETEO_TIMEOUT_TOTAL,
        connect=OPENMETEO_TIMEOUT_CONNECT
    )
}

RATE_LIMITS = {
    "openweather": {"tokens": OPENWEATHER_TOKENS, "refill_per_sec": OPENWEATHER_REFILL_RATE},
    "weatherapi": {"tokens": WEATHERAPI_TOKENS, "refill_per_sec": WEATHERAPI_REFILL_RATE},
    "openmeteo": {"tokens": OPENMETEO_TOKENS, "refill_per_sec": OPENMETEO_REFILL_RATE}
}

RETRY_CONFIG = {
    "max_retries": MAX_RETRIES,
    "base_delay": BASE_DELAY,
    "max_delay": MAX_DELAY,
    "jitter_factor": JITTER_FACTOR,
    "backoff_multiplier": BACKOFF_MULTIPLIER
}

PROVIDERS = {
    "openweather": {
        "name": "OpenWeatherMap",
        "weather_url": "https://api.openweathermap.org/data/2.5/weather",
        "geocoding_url": "http://api.openweathermap.org/geo/1.0/direct"
    },
    "weatherapi": {
        "name": "WeatherAPI",
        "weather_url": "http://api.weatherapi.com/v1/current.json"
    },
    "openmeteo": {
        "name": "OpenMeteo",
        "weather_url": "https://api.open-meteo.com/v1/forecast"
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary for debugging"""
    return {
        "retry_config": RETRY_CONFIG,
        "rate_limits": RATE_LIMITS,
        "timeouts": {
            provider: {
                "total": timeout.total,
                "connect": timeout.connect
            }
            for provider, timeout in TIMEOUTS.items()
        },
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "log_level": LOG_LEVEL,
        "api_keys_configured": {
            "openweather": bool(OPENWEATHER_API_KEY),
            "weatherapi": bool(WEATHERAPI_KEY)
        }
    }