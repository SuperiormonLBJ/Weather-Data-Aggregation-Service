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

timeouts = {
    "openweather": aiohttp.ClientTimeout(total=7, connect=2),   
    "weatherapi": aiohttp.ClientTimeout(total=7, connect=2),
    "openmeteo": aiohttp.ClientTimeout(total=8, connect=2)      # slower than other 2 API providers
}

class WeatherAggregationService:
    """Weather aggregation service - focuses on provider integration and data  aggregation"""
    
    def __init__(self):
        self.session = None

    async def get_aggregated_weather(self, location: str) -> Dict[str, Any]:
        """
        Get weather data from multiple providers in parallel and aggregate results
        """
        location = location.strip()
        
        # Validate input format and API keys
        validate_input_format(location)
        openweather_api_key, weatherapi_key = validate_api_keys()
        
        # Determine if location is coordinates or city name
        is_coords = is_coordinates(location)
        
        # Create session if not exists
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Prepare tasks for parallel execution
        tasks = []
        
        # Task 1: OpenWeatherMap
        tasks.append(self._fetch_openweather_async(location, is_coords, openweather_api_key))
        
        # Task 2: WeatherAPI
        tasks.append(self._fetch_weatherapi_async(location, weatherapi_key))
        
        # Task 3: Open-Meteo (with geocoding if needed)
        if is_coords:
            lat, lon = parse_coordinates(location)
            tasks.append(self._fetch_openmeteo_async(lat, lon))
        else:
            # Need to geocode first, then call Open-Meteo
            tasks.append(self._fetch_openmeteo_with_geocoding_async(location, openweather_api_key))
        
        # Execute all tasks in parallel
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = round((time.time() - start_time) * 1000, 2)
        
        # Process results
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
        
        if not weather_data:
            raise Exception("All weather providers failed")
        
        # Calculate median temperature
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
    
    async def _fetch_openweather_async(self, location: str, is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap asynchronously"""
        url = "https://api.openweathermap.org/data/2.5/weather"
        
        if is_coords:
            lat, lon = parse_coordinates(location)
            # unit - metric is Celsius (°C)
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric"
            }
        else:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }
        
        start = time.perf_counter()
        try:
            async with self.session.get(url, params=params, timeout=timeouts["openweather"]) as response:
                elapsed = round((time.perf_counter() - start) * 1000, 0)
                
                if response.status == 200:
                    data = await response.json()
                    description = OPENWEATHER_CODE_MAPPING[data["weather"][0]["id"]].value
                    return {
                        "name": data["name"],
                        "provider": "OpenWeatherMap",
                        "temperature": data["main"]["temp"],
                        "humidity": data["main"]["humidity"],
                        "weathercode": data["weather"][0]["id"],
                        "description": description,
                        "wind_speed": data.get("wind", {}).get("speed"),
                        "pressure": data["main"].get("pressure"),
                        "response_time (ms)": elapsed
                    }
        except Exception as e:
            raise Exception(f"OpenWeatherMap error: {str(e)}")
        
        return None
    
    async def _fetch_weatherapi_async(self, location: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from WeatherAPI.com asynchronously"""
        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": location
        }
        start = time.perf_counter()
        try:
            async with self.session.get(url, params=params, timeout=timeouts["weatherapi"]) as response:
                elapsed = round((time.perf_counter() - start) * 1000, 0)
                
                if response.status == 200:
                    data = await response.json()
                    current = data["current"]
                    description = WEATHERAPI_CODE_MAPPING[current["condition"]["code"]].value

                    return {
                        "name": data["location"]["name"],
                        "provider": "WeatherAPI",
                        "temperature": current["temp_c"],
                        "humidity": current["humidity"],
                        "weathercode": current["condition"]["code"],
                        "description": description,
                        "wind_speed (m/s)": round(current["wind_kph"] / 3.6, 2),
                        "pressure": current.get("pressure_mb"),
                        "response_time (ms)": elapsed
                    }
        except Exception as e:
            raise Exception(f"WeatherAPI error: {str(e)}")
        
        return None
    
    async def _fetch_openmeteo_async(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from Open-Meteo asynchronously"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true"
        }

        start = time.perf_counter()
        try:
            async with self.session.get(url, params=params, timeout=timeouts["openmeteo"]) as response:
                elapsed = round((time.perf_counter() - start) * 1000, 0)
                
                if response.status == 200:
                    data = await response.json()
                    current = data["current_weather"]
                    description = OPENMETEO_CODE_MAPPING[current["weathercode"]].value
                    
                    return {
                        "name": None,
                        "provider": "OpenMeteo",
                        "temperature": current["temperature"],
                        "humidity": None,
                        "weathercode": current["weathercode"],
                        "description": description,
                        "wind_speed (m/s)": round(current["windspeed"] / 3.6, 2),
                        "pressure": None,
                        "response_time (ms)": elapsed
                    }
        except Exception as e:
            raise Exception(f"OpenMeteo error: {str(e)}")
        
        return None
    
    async def _fetch_openmeteo_with_geocoding_async(self, city_name: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch Open-Meteo data with geocoding for city names"""
        try:
            # First geocode the city
            coords = await self._geocode_location_async(city_name, api_key)
            if coords:
                lat, lon = coords
                return await self._fetch_openmeteo_async(lat, lon)
        except Exception as e:
            raise Exception(f"OpenMeteo geocoding error: {str(e)}")
        
        return None
    
    async def _geocode_location_async(self, city_name: str, api_key: str) -> Optional[tuple]:
        """Get coordinates for a city name using OpenWeatherMap geocoding asynchronously"""
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": city_name,
            "limit": 1,
            "appid": api_key
        }
        
        try:
            async with self.session.get(url, params=params, timeout=timeouts["openweather"]) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return data[0]["lat"], data[0]["lon"]
        except Exception as e:
            raise Exception(f"Geocoding error: {str(e)}")
        
        return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
