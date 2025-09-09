"""
Centralized exceptions for Weather Data Aggregation Service
"""

# Base exception
class WeatherServiceError(Exception):
    """Base exception for weather service"""
    pass

# Input validation errors (400)
class ValidationError(WeatherServiceError):
    """Invalid user input - maps to HTTP 400"""
    pass

# Configuration errors (500) 
class ConfigurationError(WeatherServiceError):
    """Missing/invalid configuration - maps to HTTP 500"""
    pass

# Service errors (500)
class ProviderError(WeatherServiceError):
    """All weather providers failed - maps to HTTP 500"""
    pass

# HTTP status code mapping
def get_status_code(exception):
    """Get HTTP status code for exception"""
    if isinstance(exception, ValidationError):
        return 400
    else:
        return 500

# Error message formatting
def format_error(exception):
    """Format error message for API response"""
    if isinstance(exception, ValidationError):
        return f"Invalid input: {str(exception)}"
    elif isinstance(exception, ConfigurationError):
        return f"Configuration error: {str(exception)}"
    elif isinstance(exception, ProviderError):
        return f"Service error: {str(exception)}"
    else:
        return f"Server error: {str(exception)}"

# Response examples for Swagger documentation
RESPONSE_EXAMPLES = {
    400: {
        "description": "Bad Request - Invalid input",
        "content": {
            "application/json": {
                "examples": {
                    "invalid_coordinates": {
                        "summary": "Invalid coordinate format",
                        "value": {"detail": "Invalid input: Coordinates must be in format 'latitude,longitude'"}
                    },
                    "coordinate_range": {
                        "summary": "Coordinates out of range", 
                        "value": {"detail": "Invalid input: Latitude 91 is out of range. Must be between -90 and 90"}
                    },
                    "invalid_city": {
                        "summary": "Invalid city name",
                        "value": {"detail": "Invalid input: City name must be at least 2 characters"}
                    },
                    "empty_location": {
                        "summary": "Empty location",
                        "value": {"detail": "Invalid input: Location cannot be empty"}
                    },
                    "too_many_commas": {
                        "summary": "Too many commas",
                        "value": {"detail": "Invalid input: Too many commas. Use 'latitude,longitude' for coordinates"}
                    }
                }
            }
        }
    },
    422: {
        "description": "Validation Error - Missing required parameters",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["query", "location"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "examples": {
                    "all_providers_failed": {
                        "summary": "All weather providers failed",
                        "value": {"detail": "Service error: All weather providers failed - no data available"}
                    },
                    "missing_api_keys": {
                        "summary": "Missing API keys",
                        "value": {"detail": "Configuration error: Missing required API keys"}
                    },
                    "network_error": {
                        "summary": "Network issues",
                        "value": {"detail": "Service error: Network timeout or connection failed"}
                    }
                }
            }
        }
    }
} 