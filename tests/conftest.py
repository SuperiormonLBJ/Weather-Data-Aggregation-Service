"""
Global test configuration and fixtures
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Generator
import aiohttp

# Set test environment variables
os.environ.update({
    'OPENWEATHER_API_KEY': 'test_openweather_key',
    'WEATHERAPI_KEY': 'test_weatherapi_key',
    'API_KEYS': 'test_api_key_1,test_api_key_2',
    'LOG_LEVEL': 'DEBUG',
    'CACHE_TTL': '60'
})

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_http_session():
    """Mock HTTP session for testing"""
    session = AsyncMock(spec=aiohttp.ClientSession)
    
    # Create a mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"test": "data"})
    mock_response.headers = {}
    
    # Create a mock context manager for session.get()
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    
    # Mock the get method to return the context manager
    session.get = Mock(return_value=mock_context)
    session.close = AsyncMock()
    
    return session

@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        "openweather": {
            "name": "Singapore",
            "temperature": 28.5,
            "humidity": 75,
            "weathercode": 800,
            "description": "Clear Sky",
            "source": {"provider": "OpenWeatherMap", "status": "success", "response_time_ms": 250}
        },
        "weatherapi": {
            "name": "Singapore",
            "temperature": 29.1,
            "humidity": 78,
            "weathercode": 1000,
            "description": "Clear",
            "source": {"provider": "WeatherAPI", "status": "success", "response_time_ms": 180}
        },
        "openmeteo": {
            "name": None,
            "temperature": 28.8,
            "humidity": None,
            "weathercode": 0,
            "description": "Clear Sky",
            "source": {"provider": "OpenMeteo", "status": "success", "response_time_ms": 120}
        }
    }

@pytest.fixture
def sample_api_responses():
    """Sample API responses for mocking"""
    return {
        "openweather_success": {
            "status": "success",
            "response_time_ms": 250,
            "data": {
                "name": "Singapore",
                "main": {"temp": 28.5, "humidity": 75},
                "weather": [{"id": 800, "description": "clear sky"}]
            }
        },
        "weatherapi_success": {
            "status": "success", 
            "response_time_ms": 180,
            "data": {
                "location": {"name": "Singapore"},
                "current": {
                    "temp_c": 29.1,
                    "humidity": 78,
                    "condition": {"code": 1000, "text": "Clear"}
                }
            }
        },
        "openmeteo_success": {
            "status": "success",
            "response_time_ms": 120,
            "data": {
                "current_weather": {
                    "temperature": 28.8,
                    "weathercode": 0
                }
            }
        }
    }

@pytest.fixture
def mock_geocoding_response():
    """Mock geocoding response"""
    return {
        "status": "success",
        "response_time_ms": 150,
        "data": [{"lat": 1.3521, "lon": 103.8198, "name": "Singapore"}]
    }

@pytest.fixture(autouse=True)
def mock_cache():
    """Mock cache for all tests"""
    with patch('app.core.cache.weather_cache') as mock_cache:
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        mock_cache.clear.return_value = None
        yield mock_cache

@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger for all tests"""
    with patch('app.core.logger.get_logger') as mock_logger:
        mock_logger.return_value = Mock()
        yield mock_logger
