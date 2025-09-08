import asyncio
import aiohttp
import time
from statistics import median
from typing import List, Dict, Any, Optional


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

# Import exceptions from centralized module
from app.exceptions import (
    ValidationError, 
    ConfigurationError, 
    ProviderError, 
    AggregationError
)


class WeatherAggregationService:
    """Weather aggregation service - focuses on provider integration and data  aggregation"""
    
    def __init__(self):
        self.session = None

    async def get_aggregated_weather(self, location: str) -> Dict[str, Any]:
        """Get weather data from multiple providers in parallel and aggregate results"""
        location = location.strip()
        
        try:
            # Validate input format and API keys
            validate_input_format(location)
            openweather_api_key, weatherapi_key = validate_api_keys()
        except (ValidationError, ConfigurationError) as e:
            # Re-raise validation/config errors as-is (will become 400/500 in routes)
            raise
        
        # Determine if location is coordinates or city name
        is_coords = is_coordinates(location)
        
        # Create session if not exists
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Execute all provider tasks in parallel
            results = await self._fetch_all_providers(location, is_coords, openweather_api_key, weatherapi_key)
            
            # Process results and create response
            weather_data, all_sources = self._process_results(results)
            
            if not weather_data:
                # Create detailed error message based on failures
                error_details = self._analyze_failures(all_sources)
                raise ProviderError(
                    f"All weather providers failed - {error_details}. "
                    "This could be due to network issues, invalid location, or service outages."
                )
            
            return self._build_response(location, weather_data, all_sources)
            
        except (ProviderError, AggregationError):
            raise  # Re-raise our custom errors
        except Exception as e:
            raise WeatherServiceError(f"Unexpected error during weather data retrieval: {str(e)}") from e
    
    async def _fetch_all_providers(self, location: str, is_coords: bool, 
                                  openweather_key: str, weatherapi_key: str) -> List[Any]:
        """Fetch from all providers in parallel"""
        tasks = [
            self._fetch_openweather(location, is_coords, openweather_key),
            self._fetch_weatherapi(location, weatherapi_key),
            self._fetch_openmeteo_with_location(location, is_coords, openweather_key)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _process_results(self, results: List[Any]) -> List[Dict]:
        """Process provider results and filter successful ones"""
        weather_data = []
        
        for result in results:
            if not isinstance(result, Exception):
                weather_data.append(result)
        
        return weather_data
    
    def _build_response(self, location: str, weather_data: List[Dict]) -> Dict[str, Any]:
        """Build the final aggregated response """
        # Calculate aggregated values
        temperatures = [data["temperature"] for data in weather_data if data.get("temperature") is not None]
        median_temp = median(temperatures) if temperatures else None

        # Calculate average humidity
        humidities = [data["humidity"] for data in weather_data if data.get("humidity") is not None]
        average_humidity = sum(humidities) / len(humidities) if humidities else None

        # Calculate most common weather description
        descriptions = [data["description"] for data in weather_data if data.get("description") is not None]
        if not descriptions:
            most_common_description = "Weather data unavailable"
        else:
            most_common_description = max(set(descriptions), key=descriptions.count)
    
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
            "source": [data["source"] for data in weather_data if data["source"] is not None],
            "timestamp_sg": get_singapore_timestamp(),
        }
    
    async def _fetch_openweather(self, location: str, is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap"""
        url = PROVIDERS["openweather"]["weather_url"]
        
        if is_coords:
            lat, lon = parse_coordinates(location)
            params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        else:
            params = {"q": location, "appid": api_key, "units": "metric"}
        
        result = await make_api_request(self.session, url, params, "openweather", "OpenWeatherMap")
        
        if result["status"] == "success":
            data = result["data"]
            weather_id = data["weather"][0]["id"]
            description = get_weather_description(OPENWEATHER_CODE_MAPPING, weather_id, 
                                                data["weather"][0]["description"])
            
            return {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": description,
                "source": {"provider": "OpenWeatherMap", "status": "success", "response_time_ms": result["response_time_ms"]}
            }
        
        return {
                "temperature": None,
                "humidity": None,
                "description": None,
                "source": {"provider": "OpenWeatherMap", "status": result["status"], "response_time_ms": result["response_time_ms"]}
            }
    
    async def _fetch_weatherapi(self, location: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from WeatherAPI.com"""
        url = PROVIDERS["weatherapi"]["weather_url"]
        params = {"key": api_key, "q": location}
        
        result = await make_api_request(self.session, url, params, "weatherapi", "WeatherAPI")
        
        if result["status"] == "success":
            data = result["data"]
            current = data["current"]
            condition_code = current["condition"]["code"]
            description = get_weather_description(WEATHERAPI_CODE_MAPPING, condition_code, 
                                                current["condition"]["text"])

            return {
                "temperature": current["temp_c"],
                "humidity": current["humidity"],
                "description": description,
                "source": {"provider": "WeatherAPI", "status": "success", "response_time_ms": result["response_time_ms"]}
            }
        
        return {
                "temperature": None,
                "humidity": None,
                "description": None,
                "source": {"provider": "WeatherAPI", "status": result["status"], "response_time_ms": result["response_time_ms"]}
            }
    
    async def _fetch_openmeteo(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from Open-Meteo using coordinates"""
        url = PROVIDERS["openmeteo"]["weather_url"]
        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        
        result = await make_api_request(self.session, url, params, "openmeteo", "OpenMeteo")
        
        if result["status"] == "success":
            data = result["data"]
            current = data["current_weather"]
            weather_code = current["weathercode"]
            description = get_weather_description(OPENMETEO_CODE_MAPPING, weather_code, 
                                                f"Weather code {weather_code}")
            
            return {
                "temperature": current["temperature"],
                "humidity": None,  # Open-Meteo doesn't provide humidity
                "description": description,
                "source": {"provider": "OpenMeteo", "status": "success", "response_time_ms": result["response_time_ms"]}
            }
        
        return {
                "temperature": None,
                "humidity": None,
                "description": None,
                "source": {"provider": "OpenMeteo", "status": result["status"], "response_time_ms": result["response_time_ms"]}
            }
    
    async def _fetch_openmeteo_with_location(self, location: str, is_coords: bool, 
                                           openweather_key: str) -> Optional[Dict[str, Any]]:
        """Fetch Open-Meteo data, handling both coordinates and city names"""
        try:
            if is_coords:
                lat, lon = parse_coordinates(location)
                return await self._fetch_openmeteo(lat, lon)
            else:
                # Geocode city name first
                coords = await self._geocode_location(location, openweather_key)
                if coords:
                    lat, lon = coords
                    return await self._fetch_openmeteo(lat, lon)
                else:
                    return {
                        "temperature": None,
                        "humidity": None,
                        "description": None,
                        "source": {"provider": "OpenMeteo", "status": "failure - geocoding error", "response_time_ms": None}
                    }
        except Exception as e:
            raise Exception(f"OpenMeteo geocoding error: {str(e)}")

    
    async def _geocode_location(self, city_name: str, api_key: str) -> Optional[tuple]:
        """Get coordinates for a city name using OpenWeatherMap geocoding"""
        url = PROVIDERS["openweather"]["geocoding_url"]
        params = {"q": city_name, "limit": 1, "appid": api_key}
        
        result = await make_api_request(self.session, url, params, "openweather", "Geocoding")
        
        if result["status"] == "success" and result["data"]:
            data = result["data"][0]
            return data["lat"], data["lon"]
        
        return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
