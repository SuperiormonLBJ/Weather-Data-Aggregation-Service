"""
Utility Functions Module

This module provides core utility functions for the Weather Data Aggregation Service,
including input validation, coordinate parsing, API key validation, and timezone handling.

The utilities are designed to ensure data integrity, provide comprehensive error handling,
and maintain consistent validation rules across the entire application.

Main Categories:
    - Location Processing: Coordinate parsing and city name validation
    - Input Validation: Format checking and business rule enforcement  
    - Configuration Validation: API key and environment verification
    - Time Utilities: Timezone-aware timestamp generation

Error Handling:
    All validation functions raise specific exception types (ValidationError, 
    ConfigurationError) with descriptive messages to help with debugging and
    user feedback.

Author: Li Beiji  
Version: 1.0.0
"""
import re
from typing import Tuple
from datetime import datetime, timezone, timedelta
from ..config import OPENWEATHER_API_KEY, WEATHERAPI_KEY
from ..core.exceptions import ValidationError, ConfigurationError

# Validation Constants
MIN_CITY_NAME_LENGTH = 2
MAX_CITY_NAME_LENGTH = 100
LATITUDE_MIN = -90.0
LATITUDE_MAX = 90.0
LONGITUDE_MIN = -180.0
LONGITUDE_MAX = 180.0

# Regular Expression Patterns
COORDINATE_PATTERN = r'^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$'
SINGAPORE_UTC_OFFSET = 8  # Singapore is UTC+8


def is_coordinates(location: str) -> bool:
    """
    Determine if a location string represents geographic coordinates.
    
    This function checks whether the input string follows the coordinate format
    (latitude,longitude) with proper numeric values and exactly one comma separator.
    
    Args:
        location (str): The location string to evaluate
        
    Returns:
        bool: True if the location represents coordinates, False otherwise
        
    Expected Format:
        - "latitude,longitude" (e.g., "1.29,103.85")
        - Both values can be integers or floating-point numbers
        - Negative values are allowed for southern latitudes and western longitudes
        - Exactly one comma separator is required
        
    Examples:
        >>> is_coordinates("1.29,103.85")
        True
        >>> is_coordinates("-33.8688,151.2093")  # Sydney  
        True
        >>> is_coordinates("Singapore")
        False
        >>> is_coordinates("1.29,103.85,100")  # Too many values
        False
    """
    location = location.strip()
    
    # Must contain exactly one comma
    if location.count(',') != 1:
        return False
        
    # Validate against coordinate pattern using regex
    return bool(re.match(COORDINATE_PATTERN, location))


def parse_coordinates(location: str) -> Tuple[float, float]:
    """
    Parse and validate a coordinate string into latitude and longitude values
    """
    location = location.strip()
    
    # Check for empty input
    if not location:
        raise ValidationError("Coordinate string cannot be empty")
    
    # Validate comma separator count
    if location.count(',') != 1:
        raise ValidationError("Coordinates must be in format 'latitude,longitude'")
    
    # Split and parse coordinate components
    parts = location.split(',')
    
    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
    except ValueError:
        raise ValidationError("Both latitude and longitude must be valid numbers")
    
    # Validate latitude range
    if not (LATITUDE_MIN <= lat <= LATITUDE_MAX):
        raise ValidationError(f"Latitude {lat} is out of range. Must be between {LATITUDE_MIN} and {LATITUDE_MAX}")
    
    # Validate longitude range  
    if not (LONGITUDE_MIN <= lon <= LONGITUDE_MAX):
        raise ValidationError(f"Longitude {lon} is out of range. Must be between {LONGITUDE_MIN} and {LONGITUDE_MAX}")
        
    return lat, lon


def validate_city_name(city_name: str) -> None:
    """
    Validate a city name according to business rules and format requirements.
    
    Args:
        city_name (str): The city name to validate
        
    Raises:
        ValidationError: If the city name fails any validation rule
        
    Validation Rules:
        - Cannot be empty or whitespace-only
        - Minimum length: 2 characters
        - Maximum length: 100 characters  
        - Must contain at least one alphabetic character
        
    Examples:
        >>> validate_city_name("Singapore")  # Passes validation
        >>> validate_city_name("New York")   # Passes validation  
        >>> validate_city_name("123")        # Raises ValidationError - no letters
        >>> validate_city_name("A" * 101)    # Raises ValidationError - too long
    """
    city_name = city_name.strip()
    
    # Check for empty input
    if not city_name:
        raise ValidationError("City name cannot be empty")
    
    # Validate minimum length requirement
    if len(city_name) < MIN_CITY_NAME_LENGTH:
        raise ValidationError(f"City name must be at least {MIN_CITY_NAME_LENGTH} characters")
    
    # Validate maximum length requirement
    if len(city_name) > MAX_CITY_NAME_LENGTH:
        raise ValidationError(f"City name too long (max {MAX_CITY_NAME_LENGTH} characters)")
    
    # Ensure at least one alphabetic character is present
    if not re.search(r'[a-zA-Z]', city_name):
        raise ValidationError("City name must contain at least one letter")


def validate_input_format(location: str) -> None:
    """
    Validate the format of a location input string.
    
    This is the main validation entry point that determines the input type
    (city name or coordinates) and applies the appropriate validation rules.
    
    Args:
        location (str): Location input to validate (city name or coordinates)
        
    Raises:
        ValidationError: If the input format is invalid or fails validation rules
        
    Supported Formats:
        - City names: "Singapore", "New York", "São Paulo" 
        - Coordinates: "1.29,103.85", "-33.8688,151.2093"
        
    Examples:
        >>> validate_input_format("Singapore")      # Valid city name
        >>> validate_input_format("1.29,103.85")    # Valid coordinates
        >>> validate_input_format("1,2,3")          # Raises ValidationError - too many commas
        >>> validate_input_format("")               # Raises ValidationError - empty input
    """
    # Validate input type
    if not isinstance(location, str):
        raise ValidationError("Location must be a string")
    
    original_location = location
    location = location.strip()
    
    # Check for empty input after trimming
    if not location:
        raise ValidationError("Location cannot be empty")
    
    # Determine input type based on comma count and apply appropriate validation
    comma_count = location.count(',')
    
    if comma_count == 0:
        # Single value: treat as city name
        validate_city_name(location)
    elif comma_count == 1:
        # Two values: treat as coordinates
        if not is_coordinates(location):
            raise ValidationError("Invalid coordinate format")
        parse_coordinates(location)  # Validate coordinate ranges
    else:
        # Too many values: invalid format
        raise ValidationError("Too many commas. Use 'latitude,longitude' for coordinates")


def validate_api_keys() -> Tuple[str, str]:
    """
    Validate that required API keys are configured and available.
    
    This function checks the application configuration to ensure all necessary
    API keys for weather providers are properly set. It's typically called
    during application startup to prevent runtime failures.
    
    Returns:
        Tuple[str, str]: Validated (OpenWeatherMap key, WeatherAPI key) pair
        
    Raises:
        ConfigurationError: If any required API keys are missing or invalid
        
    Required API Keys:
        - OPENWEATHER_API_KEY: For OpenWeatherMap API access
        - WEATHERAPI_KEY: For WeatherAPI.com service access
        
    Example:
        >>> openweather_key, weatherapi_key = validate_api_keys()
        >>> # Keys are now validated and ready for use
    """
    missing_keys = []
    
    # Check OpenWeatherMap API key
    if not OPENWEATHER_API_KEY:
        missing_keys.append("OPENWEATHER_API_KEY")
        
    # Check WeatherAPI.com API key
    if not WEATHERAPI_KEY:
        missing_keys.append("WEATHERAPI_KEY")
    
    # Raise configuration error if any keys are missing
    if missing_keys:
        raise ConfigurationError(f"Missing required API keys: {', '.join(missing_keys)}")
    
    return OPENWEATHER_API_KEY, WEATHERAPI_KEY


def get_singapore_timestamp() -> str:
    """
    Generate a timestamp string in Singapore timezone (UTC+8).
    
    This function provides consistent timezone handling for the application,
    ensuring all timestamps are normalized to Singapore time regardless of
    the server's local timezone configuration.
    
    Returns:
        str: ISO format timestamp string in Singapore timezone
        
    Format:
        The returned timestamp follows ISO 8601 format with timezone information:
        "YYYY-MM-DDTHH:MM:SS.microseconds+08:00"
        
    Examples:
        >>> get_singapore_timestamp()
        "2024-01-15T14:30:25.123456+08:00"
    """
    # Create Singapore timezone object (UTC+8)
    singapore_tz = timezone(timedelta(hours=SINGAPORE_UTC_OFFSET))
    
    # Get current time in Singapore timezone
    now = datetime.now(singapore_tz)
    
    # Return ISO format timestamp with timezone information
    return now.isoformat()
