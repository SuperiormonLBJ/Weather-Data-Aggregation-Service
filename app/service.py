import asyncio
import aiohttp
import time
from statistics import median
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

from app.utils import (
    is_coordinates, 
    parse_coordinates, 
    validate_input_format, 
    validate_api_keys,
    get_singapore_timestamp
)
from app.weather_code import OPENMETEO_CODE_MAPPING, OPENWEATHER_CODE_MAPPING, WEATHERAPI_CODE_MAPPING
from app.http_helper import make_api_request, get_weather_description


class WeatherAggregationService:
    """Weather aggregation service - focuses on provider integration and data  aggregation"""
    
    def __init__(self):
        self.session = None

    async def get_aggregated_weather(self, location: str) -> Dict[str, Any]:
        """Get weather data from multiple providers in parallel and aggregate results"""
        location = location.strip()
        
        # Validate input format and API keys
        validate_input_format(location)
        openweather_api_key, weatherapi_key = validate_api_keys()
        
        # Determine if location is coordinates or city name
        is_coords = is_coordinates(location)
        
        # Create session if not exists
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Execute all provider tasks in parallel
        start_time = time.time()
        results = await self._fetch_all_providers(location, is_coords, openweather_api_key, weatherapi_key)
        total_time = round((time.time() - start_time) * 1000, 2)
        
        # Process results and create response
        weather_data, failed_providers = self._process_results(results)
        
        if not weather_data:
            raise Exception("All weather providers failed")
        
        return self._build_aggregated_response(location, weather_data, failed_providers, total_time)
    
    async def _fetch_all_providers(self, location: str, is_coords: bool, 
                                  openweather_key: str, weatherapi_key: str) -> List[Any]:
        """Fetch from all providers in parallel"""
        tasks = [
            self._fetch_openweather(location, is_coords, openweather_key),
            self._fetch_weatherapi(location, weatherapi_key),
            self._fetch_openmeteo_with_location(location, is_coords, openweather_key)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _process_results(self, results: List[Any]) -> tuple:
        """Process provider results and separate successful vs failed"""
        weather_data = []
        failed_providers = []
        provider_names = ["OpenWeatherMap", "WeatherAPI", "OpenMeteo"]
        
        for i, result in enumerate(results):
            provider_name = provider_names[i]
            
            if isinstance(result, Exception):
                failed_providers.append({
                    "provider": provider_name, 
                    "error": str(result),
                    "type": type(result).__name__
                })
            elif result is not None:
                weather_data.append(result)
        
        return weather_data, failed_providers
    
    def _build_aggregated_response(self, location: str, weather_data: List[Dict], 
                                  failed_providers: List[Dict], total_time: float) -> Dict[str, Any]:
        """Build the final aggregated response"""
        # Calculate aggregated values
        temperatures = [data["temperature"] for data in weather_data]
        median_temp = median(temperatures)

        # Calculate average humidity
        humidities = [data["humidity"] for data in weather_data if data["humidity"] is not None]
        average_humidity = sum(humidities) / len(humidities) if humidities else None

        # Calculate most common weather description
        descriptions = [data["description"] for data in weather_data]
        most_common_description = max(set(descriptions), key=descriptions.count)
        
        # Return aggregated response
        return {
            "location": location,
            "temperature": {
                "median": round(median_temp, 1),
                "unit": "celsius",
                "method": "median"
            },
            "humidity": {
                "average": round(average_humidity, 1),
                "unit": "percentage",
                "method": "average"
            },
            "conditions": most_common_description,
            "providers_used": [data["provider"] for data in weather_data],
            "weather_data": weather_data,
            "timestamp_sg": get_singapore_timestamp(),
            "total_providers": len(weather_data),
            "failed_providers": failed_providers if failed_providers else None,
            "total_response_time_ms": total_time
        }
    
    async def _fetch_openweather(self, location: str, is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap"""
        url = "https://api.openweathermap.org/data/2.5/weather"
        
        if is_coords:
            lat, lon = parse_coordinates(location)
            params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        else:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }
        
        result = await make_api_request(self.session, url, params, "openweather", "OpenWeatherMap")
        
        if result["success"]:
            data = result["data"]
            weather_id = data["weather"][0]["id"]
            description = get_weather_description(OPENWEATHER_CODE_MAPPING, weather_id, 
                                                data["weather"][0]["description"])
            
            return {
                "name": data["name"],
                "provider": "OpenWeatherMap",
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "weathercode": weather_id,
                "description": description,
                "wind_speed": data.get("wind", {}).get("speed"),
                "pressure": data["main"].get("pressure"),
                "response_time (ms)": result["elapsed_ms"]
            }
        
        return None
    
    async def _fetch_weatherapi(self, location: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from WeatherAPI.com"""
        url = "http://api.weatherapi.com/v1/current.json"
        params = {"key": api_key, "q": location}
        
        result = await make_api_request(self.session, url, params, "weatherapi", "WeatherAPI")
        
        if result["success"]:
            data = result["data"]
            current = data["current"]
            condition_code = current["condition"]["code"]
            description = get_weather_description(WEATHERAPI_CODE_MAPPING, condition_code, 
                                                current["condition"]["text"])

            return {
                "name": data["location"]["name"],
                "provider": "WeatherAPI",
                "temperature": current["temp_c"],
                "humidity": current["humidity"],
                "weathercode": condition_code,
                "description": description,
                "wind_speed (m/s)": round(current["wind_kph"] / 3.6, 2),
                "pressure": current.get("pressure_mb"),
                "response_time (ms)": result["elapsed_ms"]
            }
        
        return None
    
    async def _fetch_openmeteo(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from Open-Meteo using coordinates"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        
        result = await make_api_request(self.session, url, params, "openmeteo", "OpenMeteo")
        
        if result["success"]:
            data = result["data"]
            current = data["current_weather"]
            weather_code = current["weathercode"]
            description = get_weather_description(OPENMETEO_CODE_MAPPING, weather_code, 
                                                f"Weather code {weather_code}")
            
            return {
                "name": None,
                "provider": "OpenMeteo",
                "temperature": current["temperature"],
                "humidity": None,
                "weathercode": weather_code,
                "description": description,
                "wind_speed (m/s)": round(current["windspeed"] / 3.6, 2),
                "pressure": None,
                "response_time (ms)": result["elapsed_ms"]
            }
        
        return None
    
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
        except Exception as e:
            raise Exception(f"OpenMeteo geocoding error: {str(e)}")
        
        return None
    
    async def _geocode_location(self, city_name: str, api_key: str) -> Optional[tuple]:
        """Get coordinates for a city name using OpenWeatherMap geocoding"""
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": city_name, "limit": 1, "appid": api_key}
        
        result = await make_api_request(self.session, url, params, "openweather", "Geocoding")
        
        if result["success"] and result["data"]:
            data = result["data"][0]
            return data["lat"], data["lon"]
        
        return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
