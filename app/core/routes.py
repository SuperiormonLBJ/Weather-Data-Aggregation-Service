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
                        "location": "Singapore", 
                        "temperature": {"value": 28.5, "unit": "celsius", "method": "median"},
                        "humidity": 75.2,
                        "conditions": "Partly cloudy",
                        "source": [
                            {"provider": "OpenWeatherMap", "status": "success", "response_time_ms": 234},
                            {"provider": "WeatherAPI", "status": "success", "response_time_ms": 187},
                            {"provider": "OpenMeteo", "status": "success", "response_time_ms": 156}
                        ],
                        "timestamp_sg": "2024-01-15 14:30:25 SGT"
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
    }
)
async def get_weather(
    location: str,
    api_key: str = Depends(verify_normal_user)
) -> Dict[str, Any]:
    """Get aggregated weather data from multiple providers

    **Access Level:** Normal User or Admin
    
    **Authentication:** Bearer Token Required
    - Use `Authorization: Bearer 123` for normal user
    - Use `Authorization: Bearer abc` for admin user
    
    **Input formats:**
    Please either provide a city name or coordinates with a comma.
    - City: "Singapore", "New York" 
    - Coordinates: "1.29,103.85"
    
    **Returns:**
    - Median temperature from all providers
    - Average humidity where available
    - Most common weather condition
    - Status of all providers

    **Invalid input formats:**
    - City: "a" / "123"
    - Coordinates: "1.29,103.85,103.85" / "1.29,12222" / "12"
    
    """
    
    if not location or not location.strip():
        logger.warning("Empty location parameter")
        raise HTTPException(status_code=400, detail="Location parameter is required")
    
    weather_service = None
    try:
        weather_service = WeatherAggregationService()
        result = await weather_service.get_aggregated_weather(location.strip())
        
        logger.info(f"Weather request completed: {location}")
        return result
        
    except (ValidationError, ConfigurationError, ProviderError) as e:
        status_code = get_status_code(e)
        detail = format_error(e)
        logger.warning(f"Weather request failed: {location} - {detail}")
        raise HTTPException(status_code=status_code, detail=detail)
        
    except Exception as e:
        logger.error(f"Unexpected error: {location} - {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
        

@router.get(
    "/config",
    responses={
        200: {
            "description": "Current service configuration",
            "content": {
                "application/json": {
                    "example": {
                        "providers": ["OpenWeatherMap", "WeatherAPI", "OpenMeteo"],
                        "cache_ttl": 300,
                        "timeout": 5.0
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
                    "example": {"detail": "Admin access required"}
                }
            }
        }
    }
)
def get_current_config(api_key: str = Depends(verify_admin_user)):
    """Get current service configuration
    
    **Access Level:** Admin Only
    
    **Authentication:** Bearer Token Required
    - Use `Authorization: Bearer abc` for admin access
    
    Returns the current configuration of the weather service including
    provider settings, cache TTL, and timeout configurations.
    """

    return get_config_summary()

@router.delete(
    "/cache",
    responses={
        200: {
            "description": "Cache cleared successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Cache cleared successfully"}
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
                    "example": {"detail": "Admin access required"}
                }
            }
        }
    }
)
def clear_cache(api_key: str = Depends(verify_admin_user)):
    """Clear all cached data
    
    **Access Level:** Admin Only
    
    **Authentication:** Bearer Token Required
    - Use `Authorization: Bearer abc` for admin access
    
    Clears all cached weather data from memory. This operation
    will force fresh data to be fetched from weather providers
    on the next request.
    """
    
    from .cache import weather_cache
    weather_cache.clear()
    return {"message": "Cache cleared successfully"}