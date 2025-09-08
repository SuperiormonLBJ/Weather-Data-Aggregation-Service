from fastapi import APIRouter, HTTPException
from app.service import WeatherAggregationService

router = APIRouter()

@router.get("/weather")
async def get_weather(location: str):  # Make this async
    """
    Get aggregated weather data from multiple providers in parallel
    
    Example locations, please input either city name or coordinates:
    - City: "Singapore"
    - Coordinates(latitude,longitude): "1.29,103.85"

    Invalid input:
    - "1.29,103.85,112" -> too many parameters
    - "1.29,3000" -> longitude out of range
    - "Singapore,1.29" -> too many parameters for city name

    Return status code:
    - 200: Success
    - 400: Invalid input
    - 500: Internal server error
    """
    if not location or not location.strip():
        raise HTTPException(status_code=400, detail="Location parameter is required")
    
    try:
        weather_service = WeatherAggregationService()
        result = await weather_service.get_aggregated_weather(location.strip())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch weather data - " + str(e))
