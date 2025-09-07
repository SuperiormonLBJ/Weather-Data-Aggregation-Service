from fastapi import APIRouter, HTTPException
from .service import WeatherAggregationService

router = APIRouter()

@router.get("/weather")
def get_weather(location: str):
    """
    Get aggregated weather data from multiple providers
    
    Example locations:
    - City: "Singapore"
    - Coordinates: "1.29,103.85"
    """
    if not location or not location.strip():
        raise HTTPException(status_code=400, detail="Location parameter is required")
    
    try:
        weather_service = WeatherAggregationService()
        result = weather_service.get_aggregated_weather(location.strip())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")
