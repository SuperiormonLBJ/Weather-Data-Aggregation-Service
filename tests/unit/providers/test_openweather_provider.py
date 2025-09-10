"""
Unit tests for OpenWeatherProvider
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.providers.openweather_provider import OpenWeatherProvider
from tests.mocks.weather_apis import MockWeatherAPIs


class TestOpenWeatherProvider:
    """Test cases for OpenWeatherProvider"""
    
    @pytest.fixture
    def provider(self):
        """Create provider instance for testing"""
        return OpenWeatherProvider()
    
    @pytest.fixture
    def mock_session(self):
        """Create mock HTTP session"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_fetch_weather_city_name_success(self, provider, mock_session):
        """Test successful weather fetch for city name"""
        mock_response = MockWeatherAPIs.get_openweather_response("Singapore")
        
        # Mock make_api_request where it's imported in the base provider
        # Use the base provider's make_api_request instead of the openweather_provider's, otherwise it will fail
        with patch('app.providers.base_provider.make_api_request', 
                  return_value=mock_response) as mock_request:
            result = await provider.fetch_weather(mock_session, "Singapore", False, "test_key")
            
            assert result["name"] == "Singapore"
            assert result["temperature"] == 28.5
            assert result["humidity"] == 75
            assert result["weathercode"] == 800
            assert result["description"] == "clear"  # This is what the mapping returns
            assert result["source"]["status"] == "success"
            
            # Verify API request was made with correct parameters
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][2] == {"q": "Singapore", "appid": "test_key", "units": "metric"}
    
    @pytest.mark.asyncio
    async def test_fetch_weather_coordinates_success(self, provider, mock_session):
        """Test successful weather fetch for coordinates"""
        mock_response = MockWeatherAPIs.get_openweather_response("Singapore")
        
        with patch('app.providers.base_provider.make_api_request', 
                  return_value=mock_response) as mock_request, \
             patch('app.providers.openweather_provider.parse_coordinates', 
                  return_value=(1.3521, 103.8198)):
            
            result = await provider.fetch_weather(mock_session, "1.3521,103.8198", True, "test_key")
            
            assert result["name"] == "Singapore"
            assert result["temperature"] == 28.5
            assert result["source"]["status"] == "success"
            
            # Verify API request was made with coordinates
            call_args = mock_request.call_args
            assert call_args[0][2] == {"lat": 1.3521, "lon": 103.8198, "appid": "test_key", "units": "metric"}
    
    @pytest.mark.asyncio
    async def test_fetch_weather_failure(self, provider, mock_session):
        """Test weather fetch failure"""
        mock_response = MockWeatherAPIs.get_error_response("openweather", "timeout")
        
        with patch('app.providers.base_provider.make_api_request', 
                  return_value=mock_response):
            result = await provider.fetch_weather(mock_session, "Singapore", False, "test_key")
            
            assert result["source"]["status"] == "failure"
            assert "OpenWeatherMap" in result["source"]["provider"]
    
    @pytest.mark.asyncio
    async def test_fetch_weather_exception(self, provider, mock_session):
        """Test weather fetch with exception"""
        with patch('app.providers.base_provider.make_api_request', 
                  side_effect=Exception("Network error")):
            # The provider should catch the exception and re-raise it
            with pytest.raises(Exception, match="Network error"):
                await provider.fetch_weather(mock_session, "Singapore", False, "test_key")
    
    def test_prepare_request_params_city(self, provider):
        """Test parameter preparation for city name"""
        url, params = provider._prepare_request_params("Singapore", False, "test_key")
        
        assert "api.openweathermap.org" in url
        assert params == {"q": "Singapore", "appid": "test_key", "units": "metric"}
    
    def test_prepare_request_params_coordinates(self, provider):
        """Test parameter preparation for coordinates"""
        with patch('app.providers.openweather_provider.parse_coordinates', 
                  return_value=(1.3521, 103.8198)):
            url, params = provider._prepare_request_params("1.3521,103.8198", True, "test_key")
            
            assert "api.openweathermap.org" in url
            assert params == {"lat": 1.3521, "lon": 103.8198, "appid": "test_key", "units": "metric"}
    
    def test_process_successful_response(self, provider):
        """Test successful response processing"""
        mock_result = MockWeatherAPIs.get_openweather_response("Singapore")
        
        # Don't mock get_weather_description, let it use the real mapping
        result = provider._process_successful_response(mock_result)
        
        assert result["name"] == "Singapore"
        assert result["temperature"] == 28.5
        assert result["humidity"] == 75
        assert result["weathercode"] == 800
        assert result["description"] == "clear"  # This is what the real mapping returns
        assert result["source"]["status"] == "success"
