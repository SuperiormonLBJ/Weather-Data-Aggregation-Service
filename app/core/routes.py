"""
FastAPI Routes Module

This module defines the REST API endpoints for the Weather Data Aggregation Service.
It implements a comprehensive weather data API with role-based authentication,
detailed error handling, and extensive OpenAPI documentation.

The API provides:
    - Weather data aggregation from multiple providers
    - Administrative configuration access  
    - Cache management operations
    - Authentication information endpoints

Authentication:
    - Bearer token authentication
    - Role-based access control
    - API key validation

API Desgin:
    - Weather data aggregation -> GET /weather
    - Administrative configuration access -> GET /config
    - Cache management operations -> DELETE /cache

Author: Li Beiji
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from .service import WeatherAggregationService
from .exceptions import (
    ValidationError, 
    ConfigurationError, 
    ProviderError,
    get_status_code,
    format_error,
    RESPONSE_EXAMPLES
)
from .logger import get_logger
from ..config import get_config_summary
from .auth import verify_normal_user, verify_admin_user

logger = get_logger(__name__)
router = APIRouter()

@router.get(
    "/weather",
    status_code=200,
    responses={
        200: {
            "description": "Successful weather data retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "location": "chengdu",
                        "temperature": {
                            "value": 24.2,
                            "unit": "celsius",
                            "method": "median"
                        },
                        "humidity": 87,
                        "conditions": "overcast",
                        "sources": [
                            {
                            "provider": "OpenWeatherMap",
                            "status": "success",
                            "response_time_ms": 230
                            },
                            {
                            "provider": "WeatherAPI",
                            "status": "success",
                            "response_time_ms": 348
                            },
                            {
                            "provider": "OpenMeteo",
                            "status": "success",
                            "response_time_ms": 1250
                            }
                        ],
                        "timestamp": "2025-09-11T00:13:04.462476+08:00"
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {"detail": "Admin access required"}
                }
            }
        },
        **RESPONSE_EXAMPLES
    },
    tags=["Weather Data"],
    summary="Get aggregated weather data",
    description="Retrieve current weather information from multiple providers with intelligent aggregation"
)
async def get_weather(
    location: str,
    api_key: str = Depends(verify_normal_user)
) -> Dict[str, Any]:
    """
    Retrieve aggregated weather data from multiple providers.
    
    This endpoint fetches current weather data from multiple weather service providers
    (OpenWeatherMap, WeatherAPI.com, Open-Meteo) and returns intelligently aggregated
    results with median temperature, average humidity, and consensus weather conditions.
    
    **Authentication:** Bearer Token Required
    - Use `Authorization: Bearer 123` for normal user
    - Use `Authorization: Bearer abc` for admin user
    
    Args:
        location (str): Location query (city name or coordinates)
        api_key (str): Validated API key from authentication dependency
        
    Returns:
        Dict[str, Any]: Aggregated weather data with provider metadata
        
    Raises:
        HTTPException: 
            - 400: Invalid location format or validation error
            - 401: Authentication required or invalid API key
            - 500: All weather providers failed or internal server error
            - 503: Service temporarily unavailable
    """
    # Log the incoming request for monitoring and debugging
    logger.info(f"Weather data request initiated for location: {location}")
    
    # Validate location parameter is not empty
    if not location or not location.strip():
        logger.warning("Empty location parameter")
        raise HTTPException(status_code=400, detail="Location parameter is required")
    
    weather_service = None
    try:
        # Initialize the weather aggregation service
        weather_service = WeatherAggregationService()
        
        # Fetch aggregated weather data from all providers
        result = await weather_service.get_aggregated_weather(location.strip())
        
        logger.info(f"Weather data request completed successfully for location: {location}")
        return result
        
    except (ValidationError, ConfigurationError, ProviderError) as e:
        # Handle expected business logic errors with appropriate HTTP status codes
        status_code = get_status_code(e)
        detail = format_error(e)
        logger.warning(f"Weather request failed: {location} - {detail}")
        raise HTTPException(status_code=status_code, detail=detail)
        
    except Exception as e:
        # Handle unexpected system errors with generic 500 response
        error_message = f"Internal server error during weather data retrieval: {str(e)}"
        logger.error(f"Unexpected error processing weather request for {location}: {type(e).__name__}: {str(e)}")
        
        raise HTTPException(status_code=500, detail=error_message)


@router.get(
    "/config",
    responses={
        200: {
            "description": "Current service configuration",
            "content": {
                "application/json": {
                    "example": {
                        "service": {
                            "name": "Weather Data Aggregation Service",
                            "version": "1.0.0",
                            "environment": "production"
                        },
                        "providers": {
                            "total_available": 3,
                            "configured": ["OpenWeatherMap", "WeatherAPI", "Open-Meteo"],
                            "count_configured": 3
                        },
                        "cache": {
                            "ttl_seconds": 600,
                            "enabled": True
                        },
                        "timeouts": {
                            "openweather": "7.0s total, 2.0s connect",
                            "weatherapi": "7.0s total, 2.0s connect",
                            "openmeteo": "8.0s total, 2.0s connect"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Administrative access required",
            "content": {
                "application/json": {
                    "example": {"detail": "Administrative access required. This endpoint is restricted to admin users."}
                }
            }
        }
    },
    tags=["Administration"],
    summary="Get service configuration",
    description="Retrieve comprehensive service configuration and status information (Admin only)"
)
def get_current_config(api_key: str = Depends(verify_admin_user)) -> Dict[str, Any]:
    """
    Retrieve comprehensive service configuration information.
    
    This administrative endpoint provides detailed information about the current
    service configuration, including provider status, performance settings,
    and operational parameters. It's designed for monitoring, debugging, and
    administrative oversight.
    
    **Access Level:** Admin Only
    
    **Authentication:** Bearer Token Required
    - Use `Authorization: Bearer abc` for admin access
    
    Args:
        api_key (str): Validated admin API key from authentication dependency
        
    Returns:
        Dict[str, Any]: Comprehensive configuration summary with sanitized data
        
    Raises:
        HTTPException:
            - 401: Authentication required or invalid API key
            - 403: Administrative access required (normal user attempted access)
    """

    return get_config_summary()

@router.delete(
    "/cache",
    responses={
        200: {
            "description": "Cache cleared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Cache cleared successfully",
                        "timestamp": "2024-01-15T14:30:25+08:00",
                        "operation": "cache_clear"
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {"detail": "Administrative access required. This endpoint is restricted to admin users."}
                }
            }
        }
    },
    tags=["Administration"],
    summary="Clear weather data cache",
    description="Clear all cached weather data to force fresh data retrieval (Admin only)"
)
def clear_cache(api_key: str = Depends(verify_admin_user)) -> Dict[str, Any]:
    """
    Clear all cached weather data from memory.
    
    This administrative operation removes all cached weather data, forcing the
    service to fetch fresh data from weather providers on subsequent requests.
    This is useful for debugging, testing, or when fresh data is required
    immediately rather than waiting for cache expiration.
    
    **Access Level:** Admin Only
    
    **Authentication:** Bearer Token Required
    - Only admin users can perform cache management operations
    - Use development token 'abc' or production admin token
    - Normal users will receive 403 Forbidden error
    
    Args:
        api_key (str): Validated admin API key from authentication dependency
        
    Returns:
        Dict[str, Any]: Confirmation message with operation timestamp
        
    Raises:
        HTTPException:
            - 401: Authentication required or invalid API key  
            - 403: Administrative access required (normal user attempted access)
    """
    
    from .cache import weather_cache
    weather_cache.clear()
    
    # Generate timestamp for operation tracking
    from ..utils.utils import get_singapore_timestamp
    timestamp = get_singapore_timestamp()
    
    logger.info("Cache clear operation completed successfully")
    
    return {
        "message": "Cache cleared successfully",
        "timestamp": timestamp,
        "operation": "cache_clear"
    }

@router.get(
    "/cache/stats",
    responses={
        200: {
            "description": "Cache statistics",
            "content": {
                "application/json": {
                    "example": {
                        "hits": 100,
                        "misses": 20,
                        "total_requests": 120,
                        "hit_ratio": 83.33
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {"detail": "Administrative access required. This endpoint is restricted to admin users."}
                }
            }
        }
    },
    tags=["Administration"],
    summary="Get cache statistics",
    description="Get detailed statistics about the current cache (Admin only)"
)
def get_cache_stats(api_key: str = Depends(verify_admin_user)) -> Dict[str, Any]:
    """
    Get cache statistics.
    
    This endpoint provides detailed statistics about the current cache, including
    hits, misses, total requests, and hit ratio. It's designed for monitoring,
    debugging, and administrative oversight.
    
    **Access Level:** Admin Only
    
    **Authentication:** Bearer Token Required
    - Use `Authorization: Bearer abc` for admin access
    
    Args:
        api_key (str): Validated admin API key from authentication dependency
        
    Returns:
        Dict[str, Any]: Cache statistics with sanitized data
        
    Raises:
        HTTPException:
            - 401: Authentication required or invalid API key
            - 403: Administrative access required (normal user attempted access)
    """
    
    from .cache import weather_cache
    return weather_cache.get_stats()