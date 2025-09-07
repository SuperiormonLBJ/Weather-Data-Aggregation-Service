def get_weather_description(code):
    """Convert weather code to description or open meteo"""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear", 
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle", 
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        80: "Light rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail"
    }
    return weather_codes.get(code, "Unknown")