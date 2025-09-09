import asyncio
import aiohttp
import time
from statistics import median
from typing import List, Dict, Any, Optional

from app.core.cache import weather_cache
from app.utils.utils import (
    is_coordinates, 
    validate_input_format, 
    validate_api_keys,
    get_singapore_timestamp
)
from app.http.http_client import get_global_session
from app.core.exceptions import ProviderError
from app.core.logger import get_logger, log_time
from app.providers import OpenWeatherProvider, WeatherAPIProvider, OpenMeteoProvider

logger = get_logger(__name__)


class WeatherAggregationService:
    """Weather aggregation service - focuses on provider integration and data aggregation"""
    
    def __init__(self):
        # Initialize providers
        self.openweather_provider = OpenWeatherProvider()
        self.weatherapi_provider = WeatherAPIProvider()
        self.openmeteo_provider = OpenMeteoProvider()
        logger.debug("Service initialized with refactored providers")

    @log_time
    async def get_aggregated_weather(self, location: str) -> Dict[str, Any]:
        """Main method to get aggregated weather data"""
        start_time = time.perf_counter()
        
        try:
            location = location.strip()
            validate_input_format(location)

            # Cache check
            cached_data = weather_cache.get(location)
            if cached_data:
                logger.info(f"Cache hit for {location}")
                return cached_data

            # Cache miss
            logger.info(f"Cache miss for {location}")

            # Validate API keys
            openweather_api_key, weatherapi_key = validate_api_keys()
            
            is_coords = is_coordinates(location)
            
            # Get global session with connection pooling
            session = await get_global_session()
            
            # Fetch from all providers
            results = await self._fetch_all_providers(session, location, is_coords, openweather_api_key, weatherapi_key)
            
            # Process results to get both successful data and all source info
            weather_data, all_sources = self._process_results(results)
            
            if not weather_data:
                logger.error("All providers failed")
                raise ProviderError("All weather providers failed to return current weather data for this location now, please try again later or change location.")
            
            logger.info(f"Success: {len(weather_data)} providers returned data")
            
            # Build response with all sources
            response = self._build_response(location, weather_data, all_sources)

            # Cache the response
            weather_cache.set(location, response)
            
            elapsed_time = round((time.perf_counter() - start_time) * 1000, 0)
            logger.info(f"get_aggregated_weather took {elapsed_time}ms")
            
            return response
            
        except Exception as e:
            elapsed_time = round((time.perf_counter() - start_time) * 1000, 0)
            logger.error(f"get_aggregated_weather failed after {elapsed_time}ms: {str(e)}")
            raise
    
    async def _fetch_all_providers(self, session: aiohttp.ClientSession, location: str, is_coords: bool, 
                                  openweather_key: str, weatherapi_key: str) -> List[Any]:
        """Fetch from all providers in parallel"""
        tasks = [
            self.openweather_provider.fetch_weather(session, location, is_coords, openweather_key),
            self.weatherapi_provider.fetch_weather(session, location, is_coords, weatherapi_key),
            self.openmeteo_provider.fetch_weather(session, location, is_coords, openweather_key)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _process_results(self, results: List[Any]) -> tuple[List[Dict], List[Dict]]:
        """Process provider results and return both successful data and all source info"""
        weather_data = []
        all_sources = []
        providers = ["OpenWeatherMap", "WeatherAPI", "OpenMeteo"]
        
        for i, result in enumerate(results):
            provider = providers[i]
            
            if result and not isinstance(result, Exception) and "source" in result:
                if result["source"]["status"] == "success":
                    logger.info(f"✓ {provider} success")
                    weather_data.append(result)
                    all_sources.append(result["source"])
                else:
                    logger.warning(f"✗ {provider} failed: {result['source']['status']}")
                    all_sources.append(result["source"])
            else:
                logger.error(f"✗ {provider} failed with exception")
                all_sources.append({"provider": provider, "status": "failure with exception", "response_time_ms": 0})
        return weather_data, all_sources
    
    def _build_response(self, location: str, weather_data: List[Dict], all_sources: List[Dict]) -> Dict[str, Any]:
        """Build the final aggregated response with all provider sources"""
        # Calculate aggregated values
        logger.debug("Building response")
        temperatures = [data["temperature"] for data in weather_data if data["temperature"] is not None]
        median_temp = median(temperatures) if temperatures else None

        # Calculate average humidity
        humidities = [data["humidity"] for data in weather_data if data["humidity"] is not None]
        average_humidity = sum(humidities) / len(humidities) if humidities else None

        # Calculate most common weather description
        descriptions = [data["description"] for data in weather_data if data["description"] is not None]
        if not descriptions:
            most_common_description = "Weather data unavailable"
        else:
            most_common_description = max(set(descriptions), key=descriptions.count)

        logger.debug(f"Aggregated Done, {len(weather_data)} sources")
    
        # Return aggregated response
        return {
            "location": location,
            "temperature": {
                "value": round(median_temp, 1) if median_temp is not None else None,
                "unit": "celsius",
                "method": "median"
            },
            "humidity": round(average_humidity, 1) if average_humidity is not None else None,
            "conditions": most_common_description,
            "sources": all_sources,  # includes all providers (success + failure)
            "timestamp": get_singapore_timestamp(),
        }
