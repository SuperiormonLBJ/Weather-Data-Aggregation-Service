import re
import os
from typing import Tuple, Optional
from datetime import datetime

def is_coordinates(location: str) -> bool:
    """Check if location is in coordinate format (lat,lon)"""
    location = location.strip()
    
    # Must contain exactly one comma
    if location.count(',') != 1:
        return False
    
    # Must match the coordinate number pattern
    pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
    return bool(re.match(pattern, location))

def parse_coordinates(location: str) -> Tuple[float, float]:
    """Parse coordinate string into lat, lon"""
    parts = location.strip().split(',')
    
    if len(parts) != 2:
        raise ValueError("Coordinates must be in format 'latitude,longitude'")
    
    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        raise ValueError(f"Invalid coordinate format: '{location}'. Both latitude and longitude must be valid numbers")
    
    # Validate coordinate ranges
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} is out of range. Must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude {lon} is out of range. Must be between -180 and 180")
        
    return lat, lon

def validate_city_name(city_name: str) -> None:
    """Simple city name validation"""
    city_name = city_name.strip()
    
    # Basic checks only
    if len(city_name) < 2:
        raise ValueError("City name must be at least 2 characters")
    
    if len(city_name) > 100:
        raise ValueError("City name too long")
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', city_name):
        raise ValueError("City name must contain letters")

def validate_input_format(location: str) -> None:
    """Validate input format before processing"""
    location = location.strip()
    

    comma_count = location.count(',')

    # No comma - city name, should not be pure numbers
    if comma_count == 0:
        validate_city_name(location)

    # Too many commas
    if comma_count > 1:
        raise ValueError(f"Invalid format: '{location}'. Too many values given. Use 'latitude,longitude' for coordinates or city name without commas")
    
    # Exactly one comma - should be valid coordinates
    if comma_count == 1:
        if not is_coordinates(location):
            raise ValueError(f"Invalid coordinate format: '{location}'. Expected format: 'latitude,longitude' with valid numbers")
        
        # Also validate the coordinate values
        try:
            parse_coordinates(location)
        except ValueError as e:
            raise ValueError(f"Invalid coordinates: {str(e)}")

def validate_api_keys() -> Tuple[str, str]:
    """Validate API keys are available and return them"""
    openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
    weatherapi_key = os.getenv('WEATHERAPI_KEY')
    
    missing_keys = []
    if not openweather_api_key:
        missing_keys.append("OPENWEATHER_API_KEY")
    if not weatherapi_key:
        missing_keys.append("WEATHERAPI_KEY")
        
    if missing_keys:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}. Please check your .env file.")
    
    return openweather_api_key, weatherapi_key

def get_singapore_timestamp() -> str:
    """Get current timestamp in Singapore timezone (UTC+8)"""
    from datetime import timezone, timedelta
    
    # Singapore is UTC+8
    sg_offset = timedelta(hours=8)
    sg_timezone = timezone(sg_offset)
    sg_time = datetime.now(sg_timezone)
    return sg_time.isoformat() 