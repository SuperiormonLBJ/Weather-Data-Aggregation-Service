"""
WeatherAPI provider implementation
"""
from typing import Dict, Any, Tuple
import aiohttp
from ..config import PROVIDERS
from ..utils.weather_code import WEATHERAPI_CODE_MAPPING
from .base_provider import BaseWeatherProvider


class WeatherAPIProvider(BaseWeatherProvider):
    """WeatherAPI weather provider"""
    
    def __init__(self):
        super().__init__("WeatherAPI", "weatherapi")
    
    def _prepare_request_params(self, location: str, is_coords: bool, api_key: str) -> Tuple[str, Dict[str, Any]]:
        """
        [Over-ride] Prepare WeatherAPI request parameters
        """
        url = PROVIDERS["weatherapi"]["weather_url"]
        params = {"key": api_key, "q": location}
        return url, params
    
    def _process_successful_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Over-ride] Process WeatherAPI successful response
        """
        data = result["data"]
        current = data["current"]
        condition_code = current["condition"]["code"]
        description = self._get_weather_description(
            WEATHERAPI_CODE_MAPPING, 
            condition_code, 
            current["condition"]["text"]
        )
        
        return {
            "name": data["location"]["name"],
            "temperature": current["temp_c"],
            "humidity": current["humidity"],
            "weathercode": condition_code,
            "description": description,
            "source": {
                "provider": self.provider_name, 
                "status": "success", 
                "response_time_ms": result["response_time_ms"]
            }
        }
