"""
Utility functions for weather service
"""
import re
from typing import Tuple
from datetime import datetime, timezone, timedelta
from ..config import OPENWEATHER_API_KEY, WEATHERAPI_KEY
from ..core.exceptions import ValidationError, ConfigurationError


def is_coordinates(location: str) -> bool:
    """Check if location is in coordinate format (lat,lon)"""
    location = location.strip()
    
    # Must contain exactly one comma
    if location.count(',') != 1:
        return False
    pattern = r'^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$'
    return bool(re.match(pattern, location))


def parse_coordinates(location: str) -> Tuple[float, float]:
    """Parse and validate coordinate string"""
    location = location.strip()
    
    if not location:
        raise ValidationError("Coordinate string cannot be empty")
    
    if location.count(',') != 1:
        raise ValidationError("Coordinates must be in format 'latitude,longitude'")
    
    parts = location.split(',')
    
    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
    except ValueError:
        raise ValidationError("Both latitude and longitude must be valid numbers")
    
    # Basic validation
    if not (-90 <= lat <= 90):
        raise ValidationError(f"Latitude {lat} is out of range. Must be between -90 and 90")
    
    if not (-180 <= lon <= 180):
        raise ValidationError(f"Longitude {lon} is out of range. Must be between -180 and 180")
        
    return lat, lon


def validate_city_name(city_name: str) -> None:
    """Validate city name"""
    city_name = city_name.strip()
    
    if not city_name:
        raise ValidationError("City name cannot be empty")
    
    if len(city_name) < 2:
        raise ValidationError("City name must be at least 2 characters")
    
    if len(city_name) > 100:
        raise ValidationError("City name too long (max 100 characters)")
    
    if not re.search(r'[a-zA-Z]', city_name):
        raise ValidationError("City name must contain at least one letter")


def validate_input_format(location: str) -> None:
    """Validate input format"""
    if not isinstance(location, str):
        raise ValidationError("Location must be a string")
    
    original_location = location
    location = location.strip()
    
    if not location:
        raise ValidationError("Location cannot be empty")
    
    comma_count = location.count(',')
    
    if comma_count == 0:
        validate_city_name(location)
    elif comma_count == 1:
        if not is_coordinates(location):
            raise ValidationError("Invalid coordinate format")
        parse_coordinates(location)
    else:
        raise ValidationError("Too many commas. Use 'latitude,longitude' for coordinates")


def validate_api_keys() -> Tuple[str, str]:
    """Validate API keys using config"""
    missing_keys = []
    
    if not OPENWEATHER_API_KEY:
        missing_keys.append("OPENWEATHER_API_KEY")
    if not WEATHERAPI_KEY:
        missing_keys.append("WEATHERAPI_KEY")
    
    if missing_keys:
        raise ConfigurationError(f"Missing required API keys: {', '.join(missing_keys)}")
    
    return OPENWEATHER_API_KEY, WEATHERAPI_KEY


def get_singapore_timestamp() -> str:
    """Get current timestamp in Singapore timezone"""
    singapore_tz = timezone(timedelta(hours=8))
    now = datetime.now(singapore_tz)
    return now.isoformat()
