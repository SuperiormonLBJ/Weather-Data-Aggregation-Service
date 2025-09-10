"""
OpenMeteo provider implementation with geocoding support
"""
from typing import Dict, Any, Tuple, Optional
import aiohttp
from ..config import PROVIDERS
from ..utils.weather_code import OPENMETEO_CODE_MAPPING
from ..utils.utils import parse_coordinates
from ..http.http_helper import make_api_request
from ..core.logger import get_logger
from .base_provider import BaseWeatherProvider

logger = get_logger(__name__)


class OpenMeteoProvider(BaseWeatherProvider):
    """OpenMeteo weather provider with geocoding support"""
    
    def __init__(self):
        super().__init__("OpenMeteo", "openmeteo")
    
    async def fetch_weather(self, session: aiohttp.ClientSession, location: str, 
                           is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """
        [Over-ride] Override to handle geocoding for city names for openmeteo case

        Args:
            session: aiohttp.ClientSession
            location: str
            is_coords: bool
            api_key: str
            
        Returns:
            Optional[Dict[str, Any]] -> weather data
            
        Raises:
            Exception
            
        Note:
            - OpenMeteo API is used to fetch weather data using coordinates
            - If city name is provided, it is geocoded to coordinates first
            - If coordinates are provided, it is used directly
        """
        try:
            if is_coords:
                lat, lon = parse_coordinates(location)
                return await self._fetch_with_coordinates(session, lat, lon)
            else:
                # Geocode first
                coords = await self._geocode_location(session, location, api_key)
                if coords:
                    lat, lon = coords
                    return await self._fetch_with_coordinates(session, lat, lon)
        except Exception as e:
            logger.error(f"OpenMeteo location error: {e}")
        
        return None
    
    async def _fetch_with_coordinates(self, session: aiohttp.ClientSession, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data using coordinates

        Args:
            session: aiohttp.ClientSession
            lat: float
            lon: float
            
        Returns:
            Optional[Dict[str, Any]] -> weather data
        """
        url, params = self._prepare_request_params(f"{lat},{lon}", True, "")
        result = await make_api_request(session, url, params, self.timeout_key, self.provider_name)
        
        if result["status"] == "success":
            return self._process_successful_response(result)
        else:
            logger.error(f"✗ {self.provider_name} failed: {result}")
            return self._create_failure_response(result)
    
    def _prepare_request_params(self, location: str, is_coords: bool, api_key: str) -> Tuple[str, Dict[str, Any]]:
        """
        [Over-ride] Prepare OpenMeteo request parameters
        """
        url = PROVIDERS["openmeteo"]["weather_url"]
        
        if is_coords:
            lat, lon = parse_coordinates(location)
            params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        else:
            # This shouldn't be called for city names, but provide fallback
            params = {"current_weather": "true"}
        
        return url, params
    
    def _process_successful_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Over-ride] Process OpenMeteo successful response
        """
        data = result["data"]
        current = data["current_weather"]
        weather_code = current["weathercode"]
        description = self._get_weather_description(
            OPENMETEO_CODE_MAPPING, 
            weather_code, 
            f"Weather code {weather_code}"
        )
        
        return {
            "name": None,  # OpenMeteo doesn't provide location name
            "temperature": current["temperature"],
            "humidity": None,  # OpenMeteo doesn't provide humidity in current_weather
            "weathercode": weather_code,
            "description": description,
            "source": {
                "provider": self.provider_name, 
                "status": "success", 
                "response_time_ms": result["response_time_ms"]
            }
        }
    
    async def _geocode_location(self, session: aiohttp.ClientSession, city_name: str, api_key: str) -> Optional[Tuple[float, float]]:
        """
        Geocode city name to coordinates using OpenWeatherMap geocoding API

        Args:
            session: aiohttp.ClientSession
            city_name: str
            api_key: str
            
        Returns:
            Optional[Tuple[float, float]]
            
        Raises:
            Exception
            
        Note:
            - OpenWeatherMap geocoding API is used to geocode city names to coordinates
        """
        logger.debug(f"Geocoding: {city_name}")
        
        try:
            url = PROVIDERS["openweather"]["geocoding_url"]
            params = {"q": city_name, "limit": 1, "appid": api_key}
            
            result = await make_api_request(session, url, params, "openweather", "Geocoding")
            
            if result["status"] == "success" and result["data"]:
                data = result["data"][0]
                logger.debug(f"Geocoded to: {data['lat']}, {data['lon']}")
                return data["lat"], data["lon"]
                
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
        
        return None
