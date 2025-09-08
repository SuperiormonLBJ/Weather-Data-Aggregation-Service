import asyncio
import aiohttp
import time
from statistics import median
from typing import List, Dict, Any, Optional, Tuple


from app.cache import weather_cache
from app.utils import (
    is_coordinates, 
    parse_coordinates, 
    validate_input_format, 
    validate_api_keys,
    get_singapore_timestamp
)
from app.weather_code import OPENMETEO_CODE_MAPPING, OPENWEATHER_CODE_MAPPING, WEATHERAPI_CODE_MAPPING
from app.http_helper import make_api_request, get_weather_description
from app.config import PROVIDERS
from app.exceptions import ValidationError, ConfigurationError, ProviderError
from app.logger import get_logger, log_time

logger = get_logger(__name__)


class WeatherAggregationService:
    """Weather aggregation service - focuses on provider integration and data  aggregation"""
    
    def __init__(self):
        self.session = None
        logger.debug("Service initialized")

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
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Fetch from all providers
            results = await self._fetch_all_providers(location, is_coords, openweather_api_key, weatherapi_key)
            
            # Process results to get both successful data and all source info
            weather_data, all_sources = self._process_results(results)
            
            if not weather_data:
                logger.error("All providers failed")
                raise ProviderError("All weather providers failed to return data")
            
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
    
    async def _fetch_all_providers(self, location: str, is_coords: bool, 
                                  openweather_key: str, weatherapi_key: str) -> List[Any]:
        """Fetch from all providers in parallel"""
        tasks = [
            self._fetch_openweather(location, is_coords, openweather_key),
            self._fetch_weatherapi(location, weatherapi_key),
            self._fetch_openmeteo_with_location(location, is_coords, openweather_key)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _process_results(self, results: List[Any]) -> tuple[List[Dict], List[Dict]]:
        """Process provider results and return both successful data and all source info"""
        weather_data = []
        all_sources = []
        providers = ["OpenWeatherMap", "WeatherAPI", "OpenMeteo"]
        for i, result in enumerate(results):
            provider = providers[i]
            
            if result and not isinstance(result, Exception) and isinstance(result, dict):
                logger.info(f"✓ {provider} success")
                weather_data.append(result)
                # Add successful source info
                all_sources.append(result.get("source", {
                    "provider": provider,
                    "status": "success", 
                    "response_time_ms": result.get("response_time (ms)", 0)
                }))
            else:
                error = str(result) if isinstance(result, Exception) else "No data"
                logger.warning(f"✗ {provider} failed: {error}")
                
                # Add failed source info
                response_time = 0
                if hasattr(result, 'get') and callable(getattr(result, 'get')):
                    response_time = result.get("response_time_ms", 0)
                elif isinstance(result, dict):
                    response_time = result.get("response_time_ms", 0)
                    
                all_sources.append({
                    "provider": provider,
                    "status": "failure",
                    "response_time_ms": response_time
                })
        
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
            "humidity":round(average_humidity, 1) if average_humidity is not None else None,
            "conditions": most_common_description,
            "source": all_sources,  # Now includes all providers (success + failure)
            "timestamp_sg": get_singapore_timestamp(),
        }
    
    async def _fetch_openweather(self, location: str, is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch from OpenWeatherMap"""
        logger.debug("Fetching OpenWeatherMap")
        
        try:
            logger.debug(f"Fetching OpenWeatherMap for: {location}")
            url = PROVIDERS["openweather"]["weather_url"]
            
            if is_coords:
                lat, lon = parse_coordinates(location)
                params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
            else:
                params = {"q": location, "appid": api_key, "units": "metric"}
            
            result = await make_api_request(self.session, url, params, "openweather", "OpenWeatherMap")
            
            # FIX: Check for "status" == "success" instead of "success"
            if result["status"] == "success":
                data = result["data"]
                weather_id = data["weather"][0]["id"]
                description = get_weather_description(OPENWEATHER_CODE_MAPPING, weather_id, 
                                                    data["weather"][0]["description"])

                logger.debug(f"OpenWeatherMap success, {data['name']}")
                
                return {
                    "name": data["name"],
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "weathercode": weather_id,
                    "description": description,
                    "source": {"provider": "OpenWeatherMap", "status": "success", "response_time_ms": result["elapsed_ms"]}
                }
                
        except Exception as e:
            logger.error(f"OpenWeatherMap fetch error: {str(e)}")
        
        return {"source": {"provider": "OpenWeatherMap", "status": "failure", "response_time_ms": result["elapsed_ms"]}}
    
    async def _fetch_weatherapi(self, location: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch from WeatherAPI"""
        logger.debug("Fetching WeatherAPI")
        
        try:
            url = PROVIDERS["weatherapi"]["weather_url"]
            params = {"key": api_key, "q": location}
            
            result = await make_api_request(self.session, url, params, "weatherapi", "WeatherAPI")
            
            if result["status"] == "success":
                data = result["data"]
                current = data["current"]
                condition_code = current["condition"]["code"]
                description = get_weather_description(WEATHERAPI_CODE_MAPPING, condition_code, 
                                                    current["condition"]["text"])

                logger.debug(f"WeatherAPI success, {data['location']['name']}")

                return {
                    "name": data["location"]["name"],
                    "temperature": current["temp_c"],
                    "humidity": current["humidity"],
                    "weathercode": condition_code,
                    "description": description,
                    "source": {"provider": "WeatherAPI", "status": "success", "response_time_ms": result["elapsed_ms"]}
                }
                
        except Exception as e:
            logger.error(f"WeatherAPI error: {e}")
        
        return {"source": {"provider": "WeatherAPI", "status": "failure", "response_time_ms": result["elapsed_ms"]}}
    
    async def _fetch_openmeteo(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch from Open-Meteo"""
        logger.debug("Fetching OpenMeteo")
        
        try:
            url = PROVIDERS["openmeteo"]["weather_url"]
            params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
            
            result = await make_api_request(self.session, url, params, "openmeteo", "OpenMeteo")
            
            if result["status"] == "success":
                data = result["data"]
                current = data["current_weather"]
                weather_code = current["weathercode"]
                description = get_weather_description(OPENMETEO_CODE_MAPPING, weather_code, 
                                                    f"Weather code {weather_code}")
                
                logger.debug(f"OpenMeteo success, lat:{lat} lon:{lon}")

                return {
                    "name": None,
                    "temperature": current["temperature"],
                    "humidity": None,
                    "weathercode": weather_code,
                    "description": description,
                    "source": {"provider": "OpenMeteo", "status": "success", "response_time_ms": result["elapsed_ms"]}
                }
                
        except Exception as e:
            logger.error(f"OpenMeteo error: {e}")
        
        return {"source": {"provider": "OpenMeteo", "status": "failure", "response_time_ms": result["elapsed_ms"]}}
    
    async def _fetch_openmeteo_with_location(self, location: str, is_coords: bool, 
                                           openweather_key: str) -> Optional[Dict[str, Any]]:
        """Fetch OpenMeteo with location handling"""
        try:
            if is_coords:
                lat, lon = parse_coordinates(location)
                return await self._fetch_openmeteo(lat, lon)
            else:
                # Geocode first
                coords = await self._geocode_location(location, openweather_key)
                if coords:
                    lat, lon = coords
                    return await self._fetch_openmeteo(lat, lon)
        except Exception as e:
            logger.error(f"OpenMeteo location error: {e}")
        
        return None
    
    async def _geocode_location(self, city_name: str, api_key: str) -> Optional[tuple]:
        """Geocode city name to coordinates"""
        logger.debug(f"Geocoding: {city_name}")
        
        try:
            url = PROVIDERS["openweather"]["geocoding_url"]
            params = {"q": city_name, "limit": 1, "appid": api_key}
            
            result = await make_api_request(self.session, url, params, "openweather", "Geocoding")
            
            if result["status"] == "success" and result["data"]:
                data = result["data"][0]
                logger.debug(f"Geocoded to: {data['lat']}, {data['lon']}")
                logger.debug(f"Geocoding success, {city_name}")
                return data["lat"], data["lon"]
                
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
        
        return None
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Session closed")
