"""
Mock weather API responses
"""
from typing import Dict, Any

class MockWeatherAPIs:
    """Mock responses for weather APIs"""
    
    @staticmethod
    def get_openweather_response(location: str = "Singapore") -> Dict[str, Any]:
        """Mock OpenWeatherMap response"""
        return {
            "status": "success",
            "response_time_ms": 250,
            "data": {
                "name": location,
                "main": {
                    "temp": 28.5,
                    "humidity": 75
                },
                "weather": [{
                    "id": 800,
                    "description": "clear sky"
                }]
            }
        }
    
    @staticmethod
    def get_weatherapi_response(location: str = "Singapore") -> Dict[str, Any]:
        """Mock WeatherAPI response"""
        return {
            "status": "success",
            "response_time_ms": 180,
            "data": {
                "location": {"name": location},
                "current": {
                    "temp_c": 29.1,
                    "humidity": 78,
                    "condition": {
                        "code": 1000,
                        "text": "Clear"
                    }
                }
            }
        }
    
    @staticmethod
    def get_openmeteo_response() -> Dict[str, Any]:
        """Mock OpenMeteo response"""
        return {
            "status": "success",
            "response_time_ms": 120,
            "data": {
                "current_weather": {
                    "temperature": 28.8,
                    "weathercode": 0
                }
            }
        }
    
    @staticmethod
    def get_geocoding_response(city: str = "Singapore") -> Dict[str, Any]:
        """Mock geocoding response"""
        return {
            "status": "success",
            "response_time_ms": 150,
            "data": [{
                "lat": 1.3521,
                "lon": 103.8198,
                "name": city
            }]
        }
    
    @staticmethod
    def get_error_response(provider: str, error_type: str = "timeout") -> Dict[str, Any]:
        """Mock error response"""
        error_messages = {
            "timeout": "Request timeout after 7.0s",
            "rate_limit": "Rate limited (HTTP 429)",
            "server_error": "Server error (HTTP 500)",
            "client_error": "Client error (HTTP 400)"
        }
        
        return {
            "status": f"failure - {error_messages.get(error_type, 'Unknown error')}",
            "response_time_ms": 0,
            "error": error_messages.get(error_type, "Unknown error")
        }
