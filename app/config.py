"""
Configuration settings for the weather service
"""
import aiohttp
from typing import Dict, Any

# API Timeout configurations
TIMEOUTS = {
    "openweather": aiohttp.ClientTimeout(total=7, connect=2),   
    "weatherapi": aiohttp.ClientTimeout(total=7, connect=2),
    "openmeteo": aiohttp.ClientTimeout(total=8, connect=2) # 8 seconds timeout for openmeteo, slower than other providers
}

# Rate limiting configurations
RATE_LIMITS = {
    "openweather": {"tokens": 60, "refill_per_sec": 1.0},
    "weatherapi": {"tokens": 100, "refill_per_sec": 1.5},
    "openmeteo": {"tokens": 1000, "refill_per_sec": 10.0}
}

# Retry configurations
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 16.0,
    "jitter_factor": 0.1,
    "backoff_multiplier": 2.0
}

# Provider configurations
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