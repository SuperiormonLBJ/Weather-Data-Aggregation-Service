"""
Weather Provider Base Class Module

This module defines the abstract base class for all weather data providers in the
Weather Data Aggregation Service. It provides a standardized interface and common
functionality for integrating with various weather APIs.

The BaseWeatherProvider implements the Template Method pattern, allowing concrete
provider implementations to customize specific aspects of data fetching while
maintaining consistent behavior across all providers.

Design Patterns:
    - Template Method: Common workflow with customizable steps
    - Strategy Pattern: Interchangeable provider implementations
    - Dependency Injection: Configurable timeout and naming

Author: Li Beiji
Version: 1.0.0
"""
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from ..http.http_helper import make_api_request, get_weather_description
from ..core.logger import get_logger

logger = get_logger(__name__)


class BaseWeatherProvider(ABC):
    """
    Abstract base class for weather data providers.
    
    This class defines the contract that all weather providers must implement
    and provides common functionality for making API requests, handling responses,
    and standardizing data formats.
    
    The class follows the Template Method pattern where the main workflow is defined
    in fetch_weather(), but specific implementation details are delegated to 
    abstract methods that concrete providers must implement.
    
    Attributes:
        provider_name (str): Human-readable name of the weather provider
        timeout_key (str): Configuration key for timeout settings lookup
        
    Example:
        class MyWeatherProvider(BaseWeatherProvider):
            def __init__(self):
                super().__init__("MyWeather", "myweather")
                
            def _prepare_request_params(self, location, is_coords, api_key):
                # Implementation specific parameter preparation
                pass
                
            def _process_successful_response(self, result):
                # Implementation specific response processing  
                pass
    """
    
    def __init__(self, provider_name: str, timeout_key: str) -> None:
        """
        Initialize the weather provider with configuration parameters.
        
        Args:
            provider_name (str): Display name for the provider (e.g., "OpenWeatherMap")
            timeout_key (str): Key for looking up timeout configuration (e.g., "openweather")
            
        Note:
            The timeout_key should correspond to an entry in the TIMEOUTS configuration
            dictionary defined in the config module.
        """
        self.provider_name = provider_name
        self.timeout_key = timeout_key
        logger.debug(f"{provider_name} provider initialized")
    
    async def fetch_weather(
        self, 
        session: aiohttp.ClientSession, 
        location: str,
        is_coords: bool, 
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data from the provider's API.
        
        This is the main entry point for weather data retrieval. It orchestrates
        the complete workflow: parameter preparation, API request, response processing,
        and error handling.
        
        Args:
            session (aiohttp.ClientSession): HTTP client session for making requests
            location (str): Location query (city name or coordinates)
            is_coords (bool): Whether location represents coordinates (lat,lon)
            api_key (str): API key for authenticating with the provider
            
        Returns:
            Optional[Dict[str, Any]]: Standardized weather data dictionary or None on failure
            
        The returned dictionary contains:
            - Standard weather fields (temperature, humidity, conditions, etc.)
            - Provider metadata (name, status, response time)
            - Error information (if applicable)
            
        Raises:
            Exception: Propagates any unhandled exceptions from the API request
        """
        logger.debug(f"Starting weather data fetch for {self.provider_name}")
        logger.debug(f"Location: {location}, Coordinates: {is_coords}")
        
        try:
            # Step 1: Prepare provider-specific request parameters
            url, params = self._prepare_request_params(location, is_coords, api_key)
            logger.debug(f"{self.provider_name} prepared request: URL={url}")
            
            # Step 2: Execute the API request with retry and rate limiting
            result = await make_api_request(
                session=session,
                url=url, 
                params=params, 
                timeout_key=self.timeout_key, 
                provider_name=self.provider_name
            )
            
            # Step 3: Process the response based on success/failure status
            if result["status"] == "success":
                logger.debug(f"{self.provider_name} API request successful")
                return self._process_successful_response(result)
            else:
                logger.error(f"{self.provider_name} API request failed: {result}")
                return self._create_failure_response(result)
                
        except Exception as e:
            logger.error(f"{self.provider_name} encountered unexpected error: {type(e).__name__}: {str(e)}")
            raise
    
    @abstractmethod
    def _prepare_request_params(
        self, 
        location: str, 
        is_coords: bool, 
        api_key: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare provider-specific URL and parameters for the API request.
        
        This abstract method must be implemented by concrete provider classes
        to define how location data and API keys are formatted for their
        specific API endpoints.
        
        Args:
            location (str): Location query string
            is_coords (bool): Whether location represents coordinates  
            api_key (str): Provider API key
            
        Returns:
            Tuple[str, Dict[str, Any]]: (API endpoint URL, request parameters dict)
            
        Example Implementation:
            def _prepare_request_params(self, location, is_coords, api_key):
                url = "https://api.myweather.com/current"
                params = {
                    "key": api_key,
                    "q": location,
                    "format": "json"
                }
                return url, params
        """
        pass
    
    @abstractmethod  
    def _process_successful_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process successful API response into standardized format.
        
        This abstract method must be implemented by concrete provider classes
        to transform their API-specific response format into the standardized
        weather data format used throughout the application.
        
        Args:
            result (Dict[str, Any]): Successful API response from make_api_request()
                Contains keys: provider, status, response_time_ms, data, attempts
                
        Returns:
            Dict[str, Any]: Standardized weather data dictionary
            
        The standardized format should include:
            - name (str): Location name
            - temperature (float): Temperature in Celsius
            - humidity (float): Humidity percentage  
            - description (str): Weather condition description
            - source (Dict): Provider metadata
            
        Example Implementation:
            def _process_successful_response(self, result):
                data = result["data"]
                return {
                    "name": data["location"]["name"],
                    "temperature": data["current"]["temp_c"], 
                    "humidity": data["current"]["humidity"],
                    "description": data["current"]["condition"]["text"],
                    "source": {
                        "provider": self.provider_name,
                        "status": "success",
                        "response_time_ms": result["response_time_ms"]
                    }
                }
        """
        pass
    
    def _create_failure_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create standardized failure response for failed API requests.
        
        This method provides consistent error response formatting across all
        providers when API requests fail due to network issues, rate limiting,
        or other errors.
        
        Args:
            result (Dict[str, Any]): Failed API response from make_api_request()
                Contains keys: provider, status, response_time_ms, error (optional)
                
        Returns:
            Dict[str, Any]: Standardized failure response
            
        The failure response includes:
            - source.provider: Provider name for identification
            - source.status: "failure" status indicator
            - source.response_time_ms: Time spent on failed request
        """
        return {
            "source": {
                "provider": self.provider_name, 
                "status": "failure", 
                "response_time_ms": result.get("response_time_ms", 0)
            }
        }
    
    def _get_weather_description(
        self, 
        mapping: Dict[int, Any], 
        code: int, 
        fallback: str
    ) -> str:
        """
        Get standardized weather description from provider-specific weather code.
        
        This utility method maps provider-specific weather condition codes to
        standardized weather descriptions using predefined mapping dictionaries.
        
        Args:
            mapping (Dict[int, Any]): Weather code to description mapping
            code (int): Provider-specific weather condition code
            fallback (str): Default description if code is not found in mapping
            
        Returns:
            str: Standardized weather condition description
            
        Example:
            description = self._get_weather_description(
                OPENWEATHER_CODE_MAPPING, 
                800,  # Clear sky code
                "Unknown"
            )
            # Returns: "clear"
        """
        return get_weather_description(mapping, code, fallback)
