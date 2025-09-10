"""
Functional/Integration Tests for Weather API

These tests actually call the API endpoints and test the complete functionality.
"""

import pytest
import pytest_asyncio
import asyncio
import aiohttp
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEYS = {
    "normal": "123",
    "admin": "abc"
}

class TestWeatherAPIFunctional:
    """Functional tests"""
    
    @pytest_asyncio.fixture
    async def session(self):
        """Create HTTP session for testing"""
        async with aiohttp.ClientSession() as session:
            yield session
    @pytest.mark.asyncio
    async def test_weather_endpoint_with_city(self, session):
        """Test weather endpoint with city name"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        params = {"location": "Singapore"}
        
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "location" in data
            assert "temperature" in data
            assert "humidity" in data
            assert "conditions" in data
            assert "sources" in data
            assert "timestamp" in data
            
            # Verify temperature structure
            assert "value" in data["temperature"]
            assert "unit" in data["temperature"]
            assert "method" in data["temperature"]
            assert data["temperature"]["unit"] == "celsius"
            assert data["temperature"]["method"] == "median"
            
            # Verify source information
            assert isinstance(data["sources"], list)
            assert len(data["sources"]) > 0
            
            # Verify each source has required fields
            for source in data["sources"]:
                assert "provider" in source
                assert "status" in source
                assert "response_time_ms" in source
    @pytest.mark.asyncio
    async def test_weather_endpoint_with_coordinates(self, session):
        """Test weather endpoint with coordinates"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        params = {"location": "1.29,103.85"}  # Singapore coordinates
        
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            assert response.status == 200
            data = await response.json()
            
            # Should work with coordinates too
            assert "location" in data
            assert "temperature" in data
    @pytest.mark.asyncio
    async def test_weather_endpoint_authentication_required(self, session):
        """Test that authentication is required"""
        params = {"location": "Singapore"}
        
        # Test without authentication
        async with session.get(f"{BASE_URL}/api/v1/weather", params=params) as response:
            assert response.status == 401 or response.status == 403
        
        # Test with invalid authentication
        headers = {"Authorization": "Bearer invalid"}
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            assert response.status == 401 or response.status == 403

    @pytest.mark.asyncio
    async def test_weather_endpoint_invalid_location(self, session):
        """Test weather endpoint with invalid location"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        params = {"location": "InvalidCity12345"}
        
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            # Should either return error or empty results
            assert response.status in [200, 400, 404, 500]
    
    @pytest.mark.asyncio
    async def test_config_endpoint_admin_access(self, session):
        """Test config endpoint requires admin access"""
        headers = {"Authorization": f"Bearer {API_KEYS['admin']}"}
        
        async with session.get(f"{BASE_URL}/api/v1/config", headers=headers) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify config structure
            assert "retry_config" in data
            assert "rate_limits" in data
            assert "timeouts" in data
            assert "cache_ttl_seconds" in data
            assert "log_level" in data
            assert "api_keys_configured" in data
    
    @pytest.mark.asyncio
    async def test_config_endpoint_normal_user_denied(self, session):
        """Test config endpoint denies normal users"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        
        async with session.get(f"{BASE_URL}/api/v1/config", headers=headers) as response:
            assert response.status == 403
    
    @pytest.mark.asyncio
    async def test_cache_clear_endpoint_admin_access(self, session):
        """Test cache clear endpoint requires admin access"""
        headers = {"Authorization": f"Bearer {API_KEYS['admin']}"}
        
        async with session.delete(f"{BASE_URL}/api/v1/cache", headers=headers) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "message" in data
            assert "timestamp" in data
            assert "operation" in data
            assert data["operation"] == "cache_clear"
    
    @pytest.mark.asyncio
    async def test_cache_clear_endpoint_normal_user_denied(self, session):
        """Test cache clear endpoint denies normal users"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        
        async with session.delete(f"{BASE_URL}/api/v1/cache", headers=headers) as response:
            assert response.status == 403
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, session):
        """Test multiple concurrent requests work properly"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        locations = ["Singapore", "New York", "London", "Tokyo", "Paris"]
        
        # Create tasks for concurrent requests
        tasks = []
        for i, location in enumerate(locations):
            params = {"location": location}
            task = session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params)
            tasks.append(task)
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        for i, response in enumerate(responses):
            assert response.status == 200, f"Request {i} failed with status {response.status}"
            
            data = await response.json()
            assert "location" in data
            assert "temperature" in data
    
    @pytest.mark.asyncio
    async def test_response_time_reasonable(self, session):
        """Test that response times are reasonable"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        params = {"location": "Singapore"}
        
        start_time = time.time()
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status == 200
            assert response_time < 10.0, f"Response time {response_time:.2f}s is too slow"
            
            # Response should be reasonably fast (under 10 seconds)
            print(f"Response time: {response_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_api_documentation_accessible(self, session):
        """Test that API documentation is accessible"""
        # Test OpenAPI docs
        async with session.get(f"{BASE_URL}/docs") as response:
            assert response.status == 200
        
        # Test ReDoc
        async with session.get(f"{BASE_URL}/redoc") as response:
            assert response.status == 200
        
        # Test OpenAPI JSON
        async with session.get(f"{BASE_URL}/openapi.json") as response:
            assert response.status == 200
            data = await response.json()
            assert "openapi" in data
            assert "info" in data

# Integration test class for more complex scenarios
class TestWeatherAPIIntegration:
    """Integration tests for complete workflows"""
    
    @pytest_asyncio.fixture
    async def session(self):
        """Create HTTP session for testing"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.mark.asyncio
    async def test_complete_weather_workflow(self, session):
        """Test complete weather data workflow"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        
        # Step 1: Get weather for Singapore
        params = {"location": "Singapore"}
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify we got weather data
            assert data["location"] == "Singapore"
            assert "temperature" in data
            assert data["temperature"]["value"] is not None
            
            # Store for cache test
            first_response = data
        
        # Step 2: Get same location again (should be cached)
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            assert response.status == 200
            cached_data = await response.json()
            
            # Should be same data (cached)
            assert cached_data["location"] == first_response["location"]
            assert cached_data["temperature"]["value"] == first_response["temperature"]["value"]
        
        # Step 3: Clear cache (admin only)
        admin_headers = {"Authorization": f"Bearer {API_KEYS['admin']}"}
        async with session.delete(f"{BASE_URL}/api/v1/cache", headers=admin_headers) as response:
            assert response.status == 200
        
        # Step 4: Get weather again (should be fresh, not cached)
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            assert response.status == 200
            fresh_data = await response.json()
            
            # Should be fresh data
            assert fresh_data["location"] == "Singapore"
            assert "temperature" in fresh_data
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, session):
        """Test error handling in various scenarios"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        
        # Test invalid location
        params = {"location": "NonExistentCity12345"}
        async with session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params) as response:
            # Should handle gracefully
            assert response.status in [200, 400, 404, 500]
    
    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self, session):
        """Test rate limiting with multiple rapid requests"""
        headers = {"Authorization": f"Bearer {API_KEYS['normal']}"}
        params = {"location": "Singapore"}
        
        # Make multiple rapid requests
        start_time = time.time()
        tasks = []
        
        for i in range(10):  # 10 rapid requests
            task = session.get(f"{BASE_URL}/api/v1/weather", headers=headers, params=params)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All requests should succeed (rate limiting is internal)
        successful = sum(1 for r in responses if r.status == 200)
        print(f"Rate limiting test: {successful}/10 requests succeeded in {total_time:.2f}s")
        
        # At least some should succeed
        assert successful > 0, "No requests succeeded - rate limiting may be too strict"

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
