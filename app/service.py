from statistics import median
import time
import requests
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

class WeatherAggregationService:
    """Weather aggregation service - focuses on provider integration and data  aggregation"""
    
    def __init__(self):
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 10))

    def get_aggregated_weather(self, location: str) -> Dict[str, Any]:
        """
        Get weather data from multiple providers and aggregate results
        """
        location = location.strip()
        
        # Validate input format and API keys
        validate_input_format(location)
        openweather_api_key, weatherapi_key = validate_api_keys()
        
        # Determine if location is coordinates or city name
        is_coords = is_coordinates(location)
        
        weather_data = []
        failed_providers = []
        
        # Fetch from OpenWeatherMap - City name or coordinates
        try:
            openweather_data = self._fetch_openweather(location, is_coords, openweather_api_key)
            if openweather_data:
                weather_data.append(openweather_data)
        except Exception:
            failed_providers.append("OpenWeatherMap")
        
        # Fetch from WeatherAPI - City name or coordinates
        try:
            weatherapi_data = self._fetch_weatherapi(location, weatherapi_key)
            if weatherapi_data:
                weather_data.append(weatherapi_data)
        except Exception:
            failed_providers.append("WeatherAPI")
        
        # Fetch from Open-Meteo
        try:
            if is_coords:
                lat, lon = parse_coordinates(location)
                openmeteo_data = self._fetch_openmeteo(lat, lon)
            else:
                # For city names, get coordinates first using OpenWeatherMap geocoding
                coords = self._geocode_location(location, openweather_api_key)
                if coords:
                    lat, lon = coords
                    openmeteo_data = self._fetch_openmeteo(lat, lon)
                else:
                    openmeteo_data = None
            
            if openmeteo_data:
                weather_data.append(openmeteo_data)
        except Exception:
            failed_providers.append("OpenMeteo")
        
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
            "total_providers": len(weather_data)
        }
    
    def _fetch_openweather(self, location: str, is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap"""
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
        response = requests.get(url, params=params, timeout=self.timeout)
        elapsed = round((time.perf_counter() - start)*1000, 0)
        
        if response.status_code == 200:
            data = response.json()
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
        return None
    
    def _fetch_weatherapi(self, location: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from WeatherAPI.com"""
        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": location
        }
        start = time.perf_counter()
        response = requests.get(url, params=params, timeout=self.timeout)
        elapsed = round((time.perf_counter() - start)*1000, 0)

        
        if response.status_code == 200:
            data = response.json()
            current = data["current"]
            description = WEATHERAPI_CODE_MAPPING[current["condition"]["code"]].value

            return {
                "name": data["location"]["name"],
                "provider": "WeatherAPI",
                "temperature": current["temp_c"],
                "humidity": current["humidity"],
                "weathercode": current["condition"]["code"],
                "description": description,
                "wind_speed (m/s)": round(current["wind_kph"] / 3.6, 2),  # Convert to m/s, 2 decimals
                "pressure": current.get("pressure_mb"),
                "response_time (ms)": elapsed
            }
        return None
    
    def _fetch_openmeteo(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from Open-Meteo"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true"
        }

        start = time.perf_counter()
        response = requests.get(url, params=params, timeout=self.timeout)
        elapsed = round((time.perf_counter() - start)*1000, 0)

        
        if response.status_code == 200:
            data = response.json()
            current = data["current_weather"]
            description = OPENMETEO_CODE_MAPPING[current["weathercode"]].value
            
            return {
                "name": None, # Not available in current weather endpoint
                "provider": "OpenMeteo",
                "temperature": current["temperature"],
                "humidity": None,  # Not available in current weather endpoint
                "weathercode": current["weathercode"],
                "description": description,
                "wind_speed (m/s)": round(current["windspeed"] / 3.6, 2),  # Convert km/h to m/s, 2 decimals
                "pressure": None,  # Not available in current weather endpoint
                "response_time (ms)": elapsed
            }
        return None
    
    def _geocode_location(self, city_name: str, api_key: str) -> Optional[tuple]:
        """Get coordinates for a city name using OpenWeatherMap geocoding"""
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": city_name,
            "limit": 1,
            "appid": api_key
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
        return None
