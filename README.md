# Weather Data Aggregation Service

A professional RESTful API service that aggregates real-time weather data from multiple providers with intelligent fallback handling, rate limiting, and caching.

## 🌟 Features

- **Multi-Provider Aggregation**: Combines data from OpenWeatherMap, WeatherAPI.com, and Open-Meteo
- **Parallel Processing**: Concurrent API calls for optimal performance (1-2s total response time)
- **Smart Caching**: In-memory cache for fast read
- **Fault Tolerance**: Service continues even when some providers fail
- **Rate Limiting**: Token bucket algorithm prevents API quota exhaustion
- **Global Support**: Accepts both city names and coordinates worldwide

## 📋 Prerequisites

- **Python 3.11+**
- **API Keys** from weather providers

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-username/Weather-Data-Aggregation-Service.git
cd Weather-Data-Aggregation-Service
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv weather-env

# Activate virtual environment
# On macOS/Linux:
source weather-env/bin/activate
# On Windows:
weather-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get API Keys

Sign up for free API keys:

- **OpenWeatherMap**: [https://openweathermap.org/api](https://openweathermap.org/api) (60 calls/minute free)
- **WeatherAPI**: [https://www.weatherapi.com/signup.aspx](https://www.weatherapi.com/signup.aspx) (1M calls/month free)

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and update with your API keys
```

**.env file:**
```env
# API Keys (Required)
OPENWEATHER_API_KEY=your_openweather_api_key_here
WEATHERAPI_KEY=your_weatherapi_key_here

# Logging level configuration
DEBUG=true
LOG_LEVEL=DEBUG
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. API testing commands

```bash
# Health check
curl http://localhost:8000/health

# Get weather by city name
curl "http://localhost:8000/api/v1/weather?location=Singapore"

# Get weather by coordinates
curl "http://localhost:8000/api/v1/weather?location=1.29,103.85"

# View API documentation
open http://localhost:8000/docs
```

## 🐳 Docker Deployment

### Single Instance (Development)

```bash
# Build image
docker build -t weather-api .

# Run container and test on local port 8000
docker run -p 8000:8000 weather-api
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `REQUEST_TIMEOUT` | `10` | API request timeout in seconds |

### Cache Backends

- **`memory`**: In-memory cache (single instance only)

## 🧪 Testing

### Manual Testing

```bash
# Test different locations
curl "http://localhost:8000/api/v1/weather?location=New York"
curl "http://localhost:8000/api/v1/weather?location=40.7128,-74.0060"
curl "http://localhost:8000/api/v1/weather?location=Tokyo"

# Test cache performance
curl "http://localhost:8000/api/v1/cache/stats"

# Test provider information
curl "http://localhost:8000/api/v1/weather/providers"
```

### Load Testing 

```bash
# Install hey for load testing
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Test single endpoint
hey -n 100 -c 10 "http://localhost:8000/api/v1/weather?location=Singapore"

# Test load balancer
hey -n 1000 -c 20 http://localhost/health
```

## 📊 Monitoring & Health Checks

### Health Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed configuration (development only)
curl http://localhost:8000/config

# Cache statistics
curl http://localhost:8000/api/v1/cache/stats  --------------------------

```


## 🔒 Security

### API Key Management

```bash
# ❌ Never commit actual keys to git
echo ".env" >> .gitignore

# ✅ Use environment-specific files
cp .env.example .env
# Edit with development keys
```

## 🔗 Links

- **OpenWeatherMap API**: [https://openweathermap.org/api](https://openweathermap.org/api)
- **WeatherAPI.com**: [https://www.weatherapi.com/](https://www.weatherapi.com/)
- **Open-Meteo**: [https://open-meteo.com/](https://open-meteo.com/)
- **FastAPI Documentation**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **Docker Compose**: [https://docs.docker.com/compose/](https://docs.docker.com/compose/)


