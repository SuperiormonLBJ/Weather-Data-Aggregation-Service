"""
Unit tests for WeatherAggregationService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.core.service import WeatherAggregationService
from app.core.exceptions import ProviderError, ValidationError, ConfigurationError


class TestWeatherAggregationService:
    """Test cases for WeatherAggregationService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return WeatherAggregationService()
    
    @pytest.mark.asyncio
    async def test_get_aggregated_weather_success(self, service, sample_weather_data, mock_http_session):
        """Test successful weather aggregation"""
        # Mock the providers
        with patch.object(service.openweather_provider, 'fetch_weather', 
                         return_value=sample_weather_data["openweather"]) as mock_ow, \
             patch.object(service.weatherapi_provider, 'fetch_weather', 
                         return_value=sample_weather_data["weatherapi"]) as mock_wa, \
             patch.object(service.openmeteo_provider, 'fetch_weather', 
                         return_value=sample_weather_data["openmeteo"]) as mock_om, \
             patch('app.core.service.get_global_session', return_value=mock_http_session), \
             patch('app.core.service.validate_api_keys', return_value=('test_key1', 'test_key2')), \
             patch('app.core.service.is_coordinates', return_value=False), \
             patch('app.core.service.weather_cache.get', return_value=None), \
             patch('app.core.service.weather_cache.set'):
            
            result = await service.get_aggregated_weather("Singapore")
            
            # Verify the result structure
            assert "location" in result
            assert "temperature" in result
            assert "humidity" in result
            assert "conditions" in result
            assert "sources" in result
            assert "timestamp" in result
            
            # Verify temperature aggregation (median)
            assert result["temperature"]["value"] == 28.8  # median of 28.5, 29.1, 28.8
            assert result["temperature"]["unit"] == "celsius"
            assert result["temperature"]["method"] == "median"
            
            # Verify humidity aggregation (average)
            assert result["humidity"] == 76.5  # average of 75, 78
            
            # Verify all providers were called
            mock_ow.assert_called_once()
            mock_wa.assert_called_once()
            mock_om.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_aggregated_weather_cache_hit(self, service, sample_weather_data):
        """Test cache hit scenario"""
        cached_data = {"location": "Singapore", "temperature": {"value": 28.0}}
        
        with patch('app.core.service.weather_cache.get', return_value=cached_data):
            result = await service.get_aggregated_weather("Singapore")
            assert result == cached_data
    
    @pytest.mark.asyncio
    async def test_get_aggregated_weather_all_providers_fail(self, service, mock_http_session):
        """Test when all providers fail"""
        with patch.object(service.openweather_provider, 'fetch_weather', 
                         return_value={"source": {"provider": "OpenWeatherMap", "status": "failure"}}) as mock_ow, \
             patch.object(service.weatherapi_provider, 'fetch_weather', 
                         return_value={"source": {"provider": "WeatherAPI", "status": "failure"}}) as mock_wa, \
             patch.object(service.openmeteo_provider, 'fetch_weather', 
                         return_value={"source": {"provider": "OpenMeteo", "status": "failure"}}) as mock_om, \
             patch('app.core.service.get_global_session', return_value=mock_http_session), \
             patch('app.core.service.validate_api_keys', return_value=('test_key1', 'test_key2')), \
             patch('app.core.service.is_coordinates', return_value=False), \
             patch('app.core.service.weather_cache.get', return_value=None):
            
            with pytest.raises(ProviderError, match="All weather providers failed"):
                await service.get_aggregated_weather("Singapore")
    
    @pytest.mark.asyncio
    async def test_get_aggregated_weather_validation_error(self, service):
        """Test validation error handling"""
        with patch('app.core.service.validate_input_format', 
                  side_effect=ValidationError("Invalid location")):
            with pytest.raises(ValidationError):
                await service.get_aggregated_weather("")
    
    @pytest.mark.asyncio
    async def test_get_aggregated_weather_configuration_error(self, service):
        """Test configuration error handling"""
        with patch('app.core.service.validate_api_keys', 
                  side_effect=ConfigurationError("Missing API keys")):
            with pytest.raises(ConfigurationError):
                await service.get_aggregated_weather("Singapore")
    
    def test_process_results_success(self, service):
        """Test result processing with successful providers"""
        results = [
            {"source": {"provider": "OpenWeatherMap", "status": "success", "response_time_ms": 250}},
            {"source": {"provider": "WeatherAPI", "status": "success", "response_time_ms": 180}},
            {"source": {"provider": "OpenMeteo", "status": "failure", "response_time_ms": 0}}
        ]
        
        weather_data, all_sources = service._process_results(results)
        
        assert len(weather_data) == 2  # Only successful providers
        assert len(all_sources) == 3  # All providers (success + failure)
        assert all_sources[0]["status"] == "success"
        assert all_sources[2]["status"] == "failure"
    
    def test_build_response(self, service, sample_weather_data):
        """Test response building"""
        weather_data = [
            sample_weather_data["openweather"],
            sample_weather_data["weatherapi"],
            sample_weather_data["openmeteo"]
        ]
        all_sources = [
            sample_weather_data["openweather"]["source"],
            sample_weather_data["weatherapi"]["source"],
            sample_weather_data["openmeteo"]["source"]
        ]
        
        with patch('app.core.service.get_singapore_timestamp', return_value="2024-01-01T12:00:00+08:00"):
            result = service._build_response("Singapore", weather_data, all_sources)
            
            assert result["location"] == "Singapore"
            assert result["temperature"]["value"] == 28.8  # median
            assert result["humidity"] == 76.5  # average
            assert result["conditions"] == "Clear Sky"  # most common
            assert len(result["sources"]) == 3
            assert result["timestamp"] == "2024-01-01T12:00:00+08:00"
