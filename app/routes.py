from fastapi import APIRouter, HTTPException
from .service import WeatherAggregationService

router = APIRouter()

@router.get("/weather")
def get_weather(location: str):
    """
    Get aggregated weather data from multiple providers
    
    Example locations, please input either city name or coordinates:
    - City: "Singapore"
    - Coordinates(latitude,longitude): "1.29,103.85"

    Invalid input:
    - "1.29,103.85,112" -> too many parameters
    - "1.29,3000" -> longitude out of range
    - "Singapore,1.29" -> too many parameters for city name
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
