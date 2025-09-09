"""
Weather condition standardization system
Maps all provider-specific weather conditions to standardized categories
"""

from enum import Enum

class StandardWeatherCondition(Enum):
    """Standardized weather conditions"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    MIST = "mist"
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    DRIZZLE = "drizzle"
    LIGHT_SNOW = "light_snow"
    MODERATE_SNOW = "moderate_snow"
    HEAVY_SNOW = "heavy_snow"
    THUNDERSTORM = "thunderstorm"
    THUNDERSTORM_WITH_RAIN = "thunderstorm_with_rain"
    THUNDERSTORM_WITH_HAIL = "thunderstorm_with_hail"
    RAIN_SHOWERS = "rain_showers"
    SNOW_SHOWERS = "snow_showers"
    SLEET = "sleet"
    FREEZING_RAIN = "freezing_rain"
    BLIZZARD = "blizzard"
    SANDSTORM = "sandstorm"
    UNKNOWN = "unknown"

# Human-readable descriptions for each standard condition
STANDARD_DESCRIPTIONS = {
    StandardWeatherCondition.CLEAR: "Clear Sky",
    StandardWeatherCondition.PARTLY_CLOUDY: "Partly Cloudy",
    StandardWeatherCondition.CLOUDY: "Cloudy",
    StandardWeatherCondition.OVERCAST: "Overcast",
    StandardWeatherCondition.FOG: "Fog",
    StandardWeatherCondition.MIST: "Mist",
    StandardWeatherCondition.LIGHT_RAIN: "Light Rain",
    StandardWeatherCondition.MODERATE_RAIN: "Moderate Rain",
    StandardWeatherCondition.HEAVY_RAIN: "Heavy Rain",
    StandardWeatherCondition.DRIZZLE: "Drizzle",
    StandardWeatherCondition.LIGHT_SNOW: "Light Snow",
    StandardWeatherCondition.MODERATE_SNOW: "Moderate Snow",
    StandardWeatherCondition.HEAVY_SNOW: "Heavy Snow",
    StandardWeatherCondition.THUNDERSTORM: "Thunderstorm",
    StandardWeatherCondition.THUNDERSTORM_WITH_RAIN: "Thunderstorm with Rain",
    StandardWeatherCondition.THUNDERSTORM_WITH_HAIL: "Thunderstorm with Hail",
    StandardWeatherCondition.RAIN_SHOWERS: "Rain Showers",
    StandardWeatherCondition.SNOW_SHOWERS: "Snow Showers",
    StandardWeatherCondition.SLEET: "Sleet",
    StandardWeatherCondition.FREEZING_RAIN: "Freezing Rain",
    StandardWeatherCondition.BLIZZARD: "Blizzard",
    StandardWeatherCondition.SANDSTORM: "Sandstorm",
    StandardWeatherCondition.UNKNOWN: "Unknown"
}

# WeatherAPI condition codes to Standard Condition mapping
# Reference: https://www.weatherapi.com/docs/weather_conditions.json
WEATHERAPI_CODE_MAPPING = {
    1000: StandardWeatherCondition.CLEAR,                    # Sunny/Clear
    1003: StandardWeatherCondition.PARTLY_CLOUDY,            # Partly cloudy
    1006: StandardWeatherCondition.CLOUDY,                   # Cloudy
    1009: StandardWeatherCondition.OVERCAST,                 # Overcast
    1030: StandardWeatherCondition.MIST,                     # Mist
    1063: StandardWeatherCondition.LIGHT_RAIN,               # Patchy rain possible
    1066: StandardWeatherCondition.LIGHT_SNOW,               # Patchy snow possible
    1069: StandardWeatherCondition.SLEET,                    # Patchy sleet possible
    1072: StandardWeatherCondition.FREEZING_RAIN,            # Patchy freezing drizzle possible
    1087: StandardWeatherCondition.THUNDERSTORM,             # Thundery outbreaks possible
    1114: StandardWeatherCondition.BLIZZARD,                 # Blowing snow
    1117: StandardWeatherCondition.BLIZZARD,                 # Blizzard
    1135: StandardWeatherCondition.FOG,                      # Fog
    1147: StandardWeatherCondition.FOG,                      # Freezing fog
    1150: StandardWeatherCondition.DRIZZLE,                  # Patchy light drizzle
    1153: StandardWeatherCondition.DRIZZLE,                  # Light drizzle
    1168: StandardWeatherCondition.FREEZING_RAIN,            # Freezing drizzle
    1171: StandardWeatherCondition.FREEZING_RAIN,            # Heavy freezing drizzle
    1180: StandardWeatherCondition.LIGHT_RAIN,               # Patchy light rain
    1183: StandardWeatherCondition.LIGHT_RAIN,               # Light rain
    1186: StandardWeatherCondition.MODERATE_RAIN,            # Moderate rain at times
    1189: StandardWeatherCondition.MODERATE_RAIN,            # Moderate rain
    1192: StandardWeatherCondition.HEAVY_RAIN,               # Heavy rain at times
    1195: StandardWeatherCondition.HEAVY_RAIN,               # Heavy rain
    1198: StandardWeatherCondition.FREEZING_RAIN,            # Light freezing rain
    1201: StandardWeatherCondition.FREEZING_RAIN,            # Moderate or heavy freezing rain
    1204: StandardWeatherCondition.SLEET,                    # Light sleet
    1207: StandardWeatherCondition.SLEET,                    # Moderate or heavy sleet
    1210: StandardWeatherCondition.LIGHT_SNOW,               # Patchy light snow
    1213: StandardWeatherCondition.LIGHT_SNOW,               # Light snow
    1216: StandardWeatherCondition.MODERATE_SNOW,            # Patchy moderate snow
    1219: StandardWeatherCondition.MODERATE_SNOW,            # Moderate snow
    1222: StandardWeatherCondition.HEAVY_SNOW,               # Patchy heavy snow
    1225: StandardWeatherCondition.HEAVY_SNOW,               # Heavy snow
    1237: StandardWeatherCondition.SLEET,                    # Ice pellets
    1240: StandardWeatherCondition.RAIN_SHOWERS,             # Light rain shower
    1243: StandardWeatherCondition.RAIN_SHOWERS,             # Moderate or heavy rain shower
    1246: StandardWeatherCondition.RAIN_SHOWERS,             # Torrential rain shower
    1249: StandardWeatherCondition.SLEET,                    # Light sleet showers
    1252: StandardWeatherCondition.SLEET,                    # Moderate or heavy sleet showers
    1255: StandardWeatherCondition.SNOW_SHOWERS,             # Light snow showers
    1258: StandardWeatherCondition.SNOW_SHOWERS,             # Moderate or heavy snow showers
    1261: StandardWeatherCondition.SLEET,                    # Light showers of ice pellets
    1264: StandardWeatherCondition.SLEET,                    # Moderate or heavy showers of ice pellets
    1273: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,   # Patchy light rain with thunder
    1276: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,   # Moderate or heavy rain with thunder
    1279: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,   # Patchy light snow with thunder
    1282: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,   # Moderate or heavy snow with thunder
}

# OpenWeatherMap ID to Standard Condition mapping
# Reference: https://openweathermap.org/weather-conditions
OPENWEATHER_CODE_MAPPING = {
    # Clear
    800: StandardWeatherCondition.CLEAR,
    
    # Clouds
    801: StandardWeatherCondition.PARTLY_CLOUDY,  # few clouds
    802: StandardWeatherCondition.PARTLY_CLOUDY,  # scattered clouds
    803: StandardWeatherCondition.CLOUDY,         # broken clouds
    804: StandardWeatherCondition.OVERCAST,       # overcast clouds
    
    # Atmosphere
    701: StandardWeatherCondition.MIST,           # mist
    711: StandardWeatherCondition.FOG,            # smoke
    721: StandardWeatherCondition.FOG,            # haze
    731: StandardWeatherCondition.SANDSTORM,      # sand/dust whirls
    741: StandardWeatherCondition.FOG,            # fog
    751: StandardWeatherCondition.SANDSTORM,      # sand
    761: StandardWeatherCondition.SANDSTORM,      # dust
    762: StandardWeatherCondition.SANDSTORM,      # volcanic ash
    771: StandardWeatherCondition.RAIN_SHOWERS,   # squalls
    781: StandardWeatherCondition.THUNDERSTORM,   # tornado
    
    # Drizzle
    300: StandardWeatherCondition.DRIZZLE,        # light intensity drizzle
    301: StandardWeatherCondition.DRIZZLE,        # drizzle
    302: StandardWeatherCondition.DRIZZLE,        # heavy intensity drizzle
    310: StandardWeatherCondition.DRIZZLE,        # light intensity drizzle rain
    311: StandardWeatherCondition.DRIZZLE,        # drizzle rain
    312: StandardWeatherCondition.DRIZZLE,        # heavy intensity drizzle rain
    313: StandardWeatherCondition.RAIN_SHOWERS,   # shower rain and drizzle
    314: StandardWeatherCondition.RAIN_SHOWERS,   # heavy shower rain and drizzle
    321: StandardWeatherCondition.RAIN_SHOWERS,   # shower drizzle
    
    # Rain
    500: StandardWeatherCondition.LIGHT_RAIN,     # light rain
    501: StandardWeatherCondition.MODERATE_RAIN,  # moderate rain
    502: StandardWeatherCondition.HEAVY_RAIN,     # heavy intensity rain
    503: StandardWeatherCondition.HEAVY_RAIN,     # very heavy rain
    504: StandardWeatherCondition.HEAVY_RAIN,     # extreme rain
    511: StandardWeatherCondition.FREEZING_RAIN,  # freezing rain
    520: StandardWeatherCondition.RAIN_SHOWERS,   # light intensity shower rain
    521: StandardWeatherCondition.RAIN_SHOWERS,   # shower rain
    522: StandardWeatherCondition.RAIN_SHOWERS,   # heavy intensity shower rain
    531: StandardWeatherCondition.RAIN_SHOWERS,   # ragged shower rain
    
    # Snow
    600: StandardWeatherCondition.LIGHT_SNOW,     # light snow
    601: StandardWeatherCondition.MODERATE_SNOW,  # snow
    602: StandardWeatherCondition.HEAVY_SNOW,     # heavy snow
    611: StandardWeatherCondition.SLEET,          # sleet
    612: StandardWeatherCondition.SLEET,          # light shower sleet
    613: StandardWeatherCondition.SLEET,          # shower sleet
    615: StandardWeatherCondition.LIGHT_SNOW,     # light rain and snow
    616: StandardWeatherCondition.MODERATE_SNOW,  # rain and snow
    620: StandardWeatherCondition.SNOW_SHOWERS,   # light shower snow
    621: StandardWeatherCondition.SNOW_SHOWERS,   # shower snow
    622: StandardWeatherCondition.BLIZZARD,       # heavy shower snow
    
    # Thunderstorm
    200: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,  # thunderstorm with light rain
    201: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,  # thunderstorm with rain
    202: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,  # thunderstorm with heavy rain
    210: StandardWeatherCondition.THUNDERSTORM,            # light thunderstorm
    211: StandardWeatherCondition.THUNDERSTORM,            # thunderstorm
    212: StandardWeatherCondition.THUNDERSTORM,            # heavy thunderstorm
    221: StandardWeatherCondition.THUNDERSTORM,            # ragged thunderstorm
    230: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,  # thunderstorm with light drizzle
    231: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,  # thunderstorm with drizzle
    232: StandardWeatherCondition.THUNDERSTORM_WITH_RAIN,  # thunderstorm with heavy drizzle
}

# Open-Meteo WMO codes to Standard Condition mapping
# Reference: https://open-meteo.com/en/docs
OPENMETEO_CODE_MAPPING = {
    0: StandardWeatherCondition.CLEAR,                    # Clear sky
    1: StandardWeatherCondition.PARTLY_CLOUDY,            # Mainly clear
    2: StandardWeatherCondition.PARTLY_CLOUDY,            # Partly cloudy
    3: StandardWeatherCondition.OVERCAST,                 # Overcast
    45: StandardWeatherCondition.FOG,                     # Fog
    48: StandardWeatherCondition.FOG,                     # Depositing rime fog
    51: StandardWeatherCondition.DRIZZLE,                 # Light drizzle
    53: StandardWeatherCondition.DRIZZLE,                 # Moderate drizzle
    55: StandardWeatherCondition.DRIZZLE,                 # Dense drizzle
    56: StandardWeatherCondition.FREEZING_RAIN,           # Light freezing drizzle
    57: StandardWeatherCondition.FREEZING_RAIN,           # Dense freezing drizzle
    61: StandardWeatherCondition.LIGHT_RAIN,              # Slight rain
    63: StandardWeatherCondition.MODERATE_RAIN,           # Moderate rain
    65: StandardWeatherCondition.HEAVY_RAIN,              # Heavy rain
    66: StandardWeatherCondition.FREEZING_RAIN,           # Light freezing rain
    67: StandardWeatherCondition.FREEZING_RAIN,           # Heavy freezing rain
    71: StandardWeatherCondition.LIGHT_SNOW,              # Slight snow fall
    73: StandardWeatherCondition.MODERATE_SNOW,           # Moderate snow fall
    75: StandardWeatherCondition.HEAVY_SNOW,              # Heavy snow fall
    77: StandardWeatherCondition.LIGHT_SNOW,              # Snow grains
    80: StandardWeatherCondition.RAIN_SHOWERS,            # Slight rain showers
    81: StandardWeatherCondition.RAIN_SHOWERS,            # Moderate rain showers
    82: StandardWeatherCondition.RAIN_SHOWERS,            # Violent rain showers
    85: StandardWeatherCondition.SNOW_SHOWERS,            # Slight snow showers
    86: StandardWeatherCondition.SNOW_SHOWERS,            # Heavy snow showers
    95: StandardWeatherCondition.THUNDERSTORM,            # Thunderstorm
    96: StandardWeatherCondition.THUNDERSTORM_WITH_HAIL,  # Thunderstorm with slight hail
    99: StandardWeatherCondition.THUNDERSTORM_WITH_HAIL,  # Thunderstorm with heavy hail
}