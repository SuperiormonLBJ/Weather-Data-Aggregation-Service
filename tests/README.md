# Weather Service Testing Guide

This directory contains comprehensive tests for the Weather Data Aggregation Service.

## Test Structure

```
tests/
├── conftest.py              # Global test configuration and fixtures
├── mocks/                   # Mock objects for external dependencies
│   ├── __init__.py
│   └── weather_apis.py      # Mock weather API responses
├── unit/                    # Unit tests
│   ├── core/               # Core service tests
│   │   └── test_service.py
│   ├── utils/              # Utility function tests
│   │   └── test_utils.py
│   └── providers/          # Provider tests
│       └── test_openweather_provider.py
```

## Running Tests

### Quick Start with MAKE
```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test types
make test-unit
make test-integration
```

### Detailed Commands

#### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/core/test_service.py -v

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=term-missing
```

#### Coverage Reports
```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Generate XML coverage report
pytest tests/ --cov=app --cov-report=xml

# Coverage with missing lines
pytest tests/ --cov=app --cov-report=term-missing
```

## Test Configuration

### pytest.ini
- Configures test discovery patterns
- Sets coverage thresholds (80% minimum)
- Configures HTML and XML reports
- Sets up asyncio mode for async tests

### .coveragerc
- Excludes test files and virtual environments
- Configures HTML report settings
- Sets up XML output

## Mock Objects

### Weather API Mocks
Located in `tests/mocks/weather_apis.py`:

- `MockWeatherAPIs.get_openweather_response()` - OpenWeatherMap mock
- `MockWeatherAPIs.get_weatherapi_response()` - WeatherAPI mock  
- `MockWeatherAPIs.get_openmeteo_response()` - OpenMeteo mock
- `MockWeatherAPIs.get_geocoding_response()` - Geocoding mock
- `MockWeatherAPIs.get_error_response()` - Error response mock

### Global Fixtures
Located in `tests/conftest.py`:

- `mock_http_session` - Mock aiohttp session
- `sample_weather_data` - Sample weather data
- `sample_api_responses` - Sample API responses
- `mock_geocoding_response` - Geocoding response
- `mock_cache` - Cache mock (auto-applied)
- `mock_logger` - Logger mock (auto-applied)

## Test Categories

### Unit Tests
Test individual components in isolation:
- Service logic
- Utility functions
- Provider implementations
- Validation functions

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch
from app.module import ClassToTest

class TestClassToTest:
    @pytest.fixture
    def instance(self):
        return ClassToTest()
    
    def test_method_success(self, instance):
        # Arrange
        input_data = "test"
        
        # Act
        result = instance.method(input_data)
        
        # Assert
        assert result == expected_output
```

### Integration Test Template
```python
import pytest
from fastapi.testclient import TestClient
from app.core.main import app

class TestAPIEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_endpoint_success(self, client):
        response = client.get("/endpoint")
        assert response.status_code == 200
```

## Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies** to ensure test isolation
4. **Test both success and failure scenarios**
5. **Use fixtures** for common test data
6. **Keep tests fast** - avoid real network calls
7. **Test edge cases** and error conditions
8. **Maintain high coverage** but focus on meaningful tests

## Debugging Tests

### Run specific test with verbose output
```bash
pytest tests/unit/core/test_service.py::TestWeatherAggregationService::test_get_aggregated_weather_success -v -s
```

### Run tests with debugging
```bash
pytest tests/ --pdb
```

### Show test coverage for specific file
```bash
pytest tests/ --cov=app.core.service --cov-report=term-missing
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=app --cov-report=xml --cov-fail-under=80
```

