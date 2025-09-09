"""
Base weather provider class with common functionality
"""
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from app.http.http_helper import make_api_request, get_weather_description
from app.core.logger import get_logger

logger = get_logger(__name__)


class BaseWeatherProvider(ABC):
    """Base class for weather providers with common functionality"""
    
    def __init__(self, provider_name: str, timeout_key: str):
        self.provider_name = provider_name
        self.timeout_key = timeout_key
        logger.debug(f"{provider_name} provider initialized")
    
    async def fetch_weather(self, session: aiohttp.ClientSession, location: str, 
                           is_coords: bool, api_key: str) -> Optional[Dict[str, Any]]:
        """Main method to fetch weather data"""
        logger.debug(f"Fetching {self.provider_name}")
        
        try:
            # Prepare parameters based on provider type
            url, params = self._prepare_request_params(location, is_coords, api_key)
            
            # Make API request
            result = await make_api_request(session, url, params, self.timeout_key, self.provider_name)
            
            # Process the result
            if result["status"] == "success":
                return self._process_successful_response(result)
            else:
                logger.error(f"✗ {self.provider_name} failed: {result}")
                return self._create_failure_response(result)
                
        except Exception as e:
            logger.error(f"{self.provider_name} fetch error: {str(e)}")
            raise
    
    @abstractmethod
    def _prepare_request_params(self, location: str, is_coords: bool, api_key: str) -> Tuple[str, Dict[str, Any]]:
        """Prepare URL and parameters for the API request"""
        pass
    
    @abstractmethod
    def _process_successful_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process successful API response into standardized format"""
        pass
    
    def _create_failure_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized failure response"""
        return {
            "source": {
                "provider": self.provider_name, 
                "status": "failure", 
                "response_time_ms": result.get("response_time_ms", 0)
            }
        }
    
    def _get_weather_description(self, mapping: Dict, code: int, fallback: str) -> str:
        """Get weather description from mapping with fallback"""
        return get_weather_description(mapping, code, fallback)
