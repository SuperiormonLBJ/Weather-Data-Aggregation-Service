import requests
import re
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from app import get_weather_description

class WeatherAggregationService:
    """weather aggregation service"""
    
    def __init__(self):
        # Load API keys from environment variables
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.weatherapi_key = os.getenv('WEATHERAPI_KEY')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 10))
        
        # Only validate when actually using the service
        self._validated = False
    
    def _validate_api_keys(self):
        """Validate API keys are available"""
        if self._validated:
            return
            
        missing_keys = []
        if not self.openweather_api_key:
            missing_keys.append("OPENWEATHER_API_KEY")
        if not self.weatherapi_key:
            missing_keys.append("WEATHERAPI_KEY")
            
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}. Please check your .env file.")
        
        self._validated = True
    
    def get_aggregated_weather(self, location: str) -> Dict[str, Any]:
        """
        Get weather data from multiple providers and aggregate results
        """
        # Validate API keys before making requests
        self._validate_api_keys()
        
        # Determine if location is coordinates or city name
        is_coords = self._is_coordinates(location)
        
        # VALIDATE COORDINATES EARLY - before calling providers, raise value error if invalid
        if is_coords:
            try:
                self._parse_coordinates(location)  # This will raise ValueError if invalid
            except ValueError as e:
                raise ValueError(f"Invalid coordinates: {str(e)}. Latitude must be between -90 and 90, longitude between -180 and 180.")
        
        weather_data = []
        failed_providers = []
        
        # Fetch from OpenWeatherMap - City name or coordinates
        try:
            openweather_data = self._fetch_openweather(location, is_coords)
            print(f"OpenWeatherMap data: {openweather_data}")
            if openweather_data:
                weather_data.append(openweather_data)
        except Exception:
            failed_providers.append("OpenWeatherMap")
        
        # Fetch from WeatherAPI - City name or coordinates
        try:
            weatherapi_data = self._fetch_weatherapi(location)
            print(f"OpenWeatherMap data: {openweather_data}")
            if weatherapi_data:
                weather_data.append(weatherapi_data)
        except Exception:
            failed_providers.append("WeatherAPI")
        
        # Fetch from Open-Meteo - Coordinates only, need to get coordinates from OpenWeatherMap geocoding
        try:
            if is_coords:
                lat, lon = self._parse_coordinates(location)
                openmeteo_data = self._fetch_openmeteo(lat, lon)
            else:
                # For city names, get coordinates first using OpenWeatherMap geocoding
                coords = self._geocode_location(location)
                if coords:
                    lat, lon = coords
                    openmeteo_data = self._fetch_openmeteo(lat, lon)
                else:
                    openmeteo_data = None
            
            if openmeteo_data:
                print(f"OpenWeatherMap data: {openweather_data}")
                weather_data.append(openmeteo_data)
        except Exception:
            failed_providers.append("OpenMeteo")
        
        # return error if all providers failed -> weather data is empty
        if not weather_data:
            raise Exception("All weather providers failed")
        
        # Calculate average temperature
        temperatures = [data["temperature"] for data in weather_data]
        average_temp = sum(temperatures) / len(temperatures)

        # get SG timezone
        sg_offset = timedelta(hours=8)
        sg_timezone = timezone(sg_offset)
        sg_time = datetime.now(sg_timezone)
        
        # Return aggregated response
        return {
            "location": location,
            "providers_used": [data["provider"] for data in weather_data],
            "weather_data": weather_data,
            "average_temperature": round(average_temp, 1),
            "search_timestamp_string": sg_time.isoformat(),
            "total_providers": len(weather_data)
        }
    
    def _fetch_openweather(self, location: str, is_coords: bool) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap"""
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        
        if is_coords:
            lat, lon = self._parse_coordinates(location)
            # unit - metric is Celsius (°C)
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
        else:
            params = {
                "q": location,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
        
        response = requests.get(base_url, params=params, timeout=self.timeout)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "provider": "OpenWeatherMap",
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed (m/s)": data.get("wind", {}).get("speed"),
                "pressure": data["main"].get("pressure")
            }
        return None
    
    def _fetch_weatherapi(self, location: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from WeatherAPI.com"""
        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": self.weatherapi_key,
            "q": location
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        
        if response.status_code == 200:
            data = response.json()
            current = data["current"]
            return {
                "provider": "WeatherAPI",
                "temperature": current["temp_c"],
                "humidity": current["humidity"],
                "description": current["condition"]["text"],
                "wind_speed (m/s)": round(current["wind_kph"] / 3.6, 2),  # Convert to m/s
                "pressure": current.get("pressure_mb")
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
        
        response = requests.get(url, params=params, timeout=self.timeout)
        
        if response.status_code == 200:
            data = response.json()
            current = data["current_weather"]
            
            description = get_weather_description(current["weathercode"])
            
            return {
                "provider": "OpenMeteo",
                "temperature": current["temperature"],
                "humidity": None,  # Not available in current weather endpoint
                "description": description,
                "wind_speed": current["windspeed"] / 3.6,  # Convert km/h to m/s
                "pressure": None  # Not available in current weather endpoint
            }
        return None
    
    def _geocode_location(self, city_name: str) -> Optional[tuple]:
        """Get coordinates for a city name using OpenWeatherMap geocoding"""
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": city_name,
            "limit": 1,
            "appid": self.openweather_api_key
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
        return None
    
    def _is_coordinates(self, location: str) -> bool:
        """Check if location is in coordinate format (lat,lon)"""
        pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
        return bool(re.match(pattern, location.strip()))
    
    def _parse_coordinates(self, location: str) -> tuple:
        """Parse coordinate string into lat, lon"""
        parts = location.strip().split(',')
        
        if len(parts) != 2:
            raise ValueError("Coordinates must be in format 'latitude,longitude'")
        
        lat = float(parts[0])
        lon = float(parts[1])
        
        # Basic validation
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid coordinates")
        
        return lat, lon
