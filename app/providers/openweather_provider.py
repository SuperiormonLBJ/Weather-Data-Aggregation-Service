"""
OpenWeatherMap provider implementation
"""
from typing import Dict, Any, Tuple
import aiohttp
from app.config import PROVIDERS
from app.utils.weather_code import OPENWEATHER_CODE_MAPPING
from app.utils.utils import parse_coordinates
from app.core.logger import get_logger
from .base_provider import BaseWeatherProvider

logger = get_logger(__name__)


class OpenWeatherProvider(BaseWeatherProvider):
    """OpenWeatherMap weather provider"""
    
    def __init__(self):
        super().__init__("OpenWeatherMap", "openweather")
    
    def _prepare_request_params(self, location: str, is_coords: bool, api_key: str) -> Tuple[str, Dict[str, Any]]:
        """Prepare OpenWeatherMap request parameters"""
        url = PROVIDERS["openweather"]["weather_url"]
        
        if is_coords:
            lat, lon = parse_coordinates(location)
            params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        else:
            params = {"q": location, "appid": api_key, "units": "metric"}
        
        return url, params
    
    def _process_successful_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpenWeatherMap successful response"""
        data = result["data"]
        weather_id = data["weather"][0]["id"]
        description = self._get_weather_description(
            OPENWEATHER_CODE_MAPPING, 
            weather_id, 
            data["weather"][0]["description"]
        )
        
        return {
            "name": data["name"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "weathercode": weather_id,
            "description": description,
            "source": {
                "provider": self.provider_name, 
                "status": "success", 
                "response_time_ms": result["response_time_ms"]
            }
        }
