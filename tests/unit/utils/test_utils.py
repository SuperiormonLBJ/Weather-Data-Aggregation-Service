"""
Unit tests for utility functions
"""
import pytest
from unittest.mock import patch
from app.utils.utils import (
    is_coordinates, 
    parse_coordinates, 
    validate_city_name,
    validate_input_format,
    validate_api_keys,
    get_singapore_timestamp
)
from app.core.exceptions import ValidationError, ConfigurationError


class TestUtils:
    """Test cases for utility functions"""
    
    def test_is_coordinates_valid(self):
        """Test valid coordinate detection"""
        assert is_coordinates("1.3521,103.8198") == True
        assert is_coordinates("-90.0,180.0") == True
        assert is_coordinates("0,0") == True
        assert is_coordinates("45.123456,-123.456789") == True
    
    def test_is_coordinates_invalid(self):
        """Test invalid coordinate detection"""
        assert is_coordinates("Singapore") == False
        assert is_coordinates("1.3521") == False
        assert is_coordinates("1.3521,103.8198,extra") == False
        assert is_coordinates("") == False
        assert is_coordinates("1.3521,") == False
        assert is_coordinates(",103.8198") == False
        assert is_coordinates("abc,def") == False
    
    def test_parse_coordinates_valid(self):
        """Test valid coordinate parsing"""
        lat, lon = parse_coordinates("1.3521,103.8198")
        assert lat == 1.3521
        assert lon == 103.8198
        
        lat, lon = parse_coordinates("-90.0,180.0")
        assert lat == -90.0
        assert lon == 180.0
    
    def test_parse_coordinates_invalid_format(self):
        """Test invalid coordinate format"""
        with pytest.raises(ValidationError, match="Coordinates must be in format"):
            parse_coordinates("1.3521")
        
        with pytest.raises(ValidationError, match="Coordinates must be in format 'latitude,longitude'"):
            parse_coordinates("1.3521,103.8198,extra")
        
        with pytest.raises(ValidationError, match="Both latitude and longitude must be valid numbers"):
            parse_coordinates("abc,def")
    
    def test_parse_coordinates_invalid_range(self):
        """Test coordinate range validation"""
        with pytest.raises(ValidationError, match="Latitude 91.0 is out of range"):
            parse_coordinates("91,103.8198")
        
        with pytest.raises(ValidationError, match="Latitude -91.0 is out of range"):
            parse_coordinates("-91,103.8198")
        
        with pytest.raises(ValidationError, match="Longitude 181.0 is out of range"):
            parse_coordinates("1.3521,181")
        
        with pytest.raises(ValidationError, match="Longitude -181.0 is out of range"):
            parse_coordinates("1.3521,-181")
    
    def test_validate_city_name_valid(self):
        """Test valid city name validation"""
        validate_city_name("Singapore")
        validate_city_name("New York")
        validate_city_name("São Paulo")
        validate_city_name("AB")  # Two characters should pass
    
    def test_validate_city_name_invalid(self):
        """Test invalid city name validation"""
        with pytest.raises(ValidationError, match="City name cannot be empty"):
            validate_city_name("")
        
        with pytest.raises(ValidationError, match="City name must be at least 2 characters"):
            validate_city_name("A")
        
        with pytest.raises(ValidationError, match="City name too long"):
            validate_city_name("A" * 101)
        
        with pytest.raises(ValidationError, match="City name must contain at least one letter"):
            validate_city_name("123")
    
    def test_validate_input_format_coordinates(self):
        """Test coordinate input validation"""
        validate_input_format("1.3521,103.8198")
        validate_input_format("-90.0,180.0")
    
    def test_validate_input_format_city(self):
        """Test city input validation"""
        validate_input_format("Singapore")
        validate_input_format("New York")
    
    def test_validate_input_format_invalid(self):
        """Test invalid input validation"""
        with pytest.raises(ValidationError, match="Location cannot be empty"):
            validate_input_format("")
        
        with pytest.raises(ValidationError, match="Too many commas"):
            validate_input_format("1.3521,103.8198,extra")
        
        with pytest.raises(ValidationError, match="Location must be a string"):
            validate_input_format(123)
    
    def test_validate_api_keys_success(self):
        """Test successful API key validation"""
        with patch('app.utils.utils.OPENWEATHER_API_KEY', 'test_key1'), \
             patch('app.utils.utils.WEATHERAPI_KEY', 'test_key2'):
            key1, key2 = validate_api_keys()
            assert key1 == 'test_key1'
            assert key2 == 'test_key2'
    
    def test_validate_api_keys_missing(self):
        """Test missing API key validation"""
        with patch('app.utils.utils.OPENWEATHER_API_KEY', None), \
             patch('app.utils.utils.WEATHERAPI_KEY', 'test_key2'):
            with pytest.raises(ConfigurationError, match="Missing required API keys"):
                validate_api_keys()
    
    def test_get_singapore_timestamp(self):
        """Test Singapore timestamp generation"""
        timestamp = get_singapore_timestamp()
        assert isinstance(timestamp, str)
        assert 'T' in timestamp  # ISO format
        assert '+' in timestamp or 'Z' in timestamp  # Timezone info
