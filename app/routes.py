from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from app.service import WeatherAggregationService
from app.exceptions import (
    ValidationError, 
    ConfigurationError, 
    ProviderError,
    get_status_code,
    format_error,
    RESPONSE_EXAMPLES
)
from app.logger import get_logger
from app.config import get_config_summary

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
        **RESPONSE_EXAMPLES
    }
)
async def get_weather(location: str) -> Dict[str, Any]:
    """Get aggregated weather data from multiple providers

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
    logger.info(f"Weather request started: {location}")
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
        

@router.get("/config")
def get_current_config():
    """Get current service configuration"""
    return get_config_summary()

@router.delete("/cache")
def clear_cache():
    """Clear all cached data"""
    from app.cache import weather_cache
    weather_cache.clear()
    return {"message": "Cache cleared successfully"}
