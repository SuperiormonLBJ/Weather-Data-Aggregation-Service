# Weather Data Aggregation Service

A professional RESTful API service that aggregates real-time weather data from 3 providers with intelligent fallback handling, rate limiting, RBAC and caching.

## 🌟 Features/Highlights

- **Multi-Provider Aggregation**: Combines data from OpenWeatherMap, WeatherAPI.com, and Open-Meteo
- **Parallel Processing**: Concurrent Async API calls for optimal performance (1-2s total response time)
- **Persistent Session Management**: Reuse connection more efficiently and cut down waiting time
- **Smart Caching**: In-memory cache for fast read
- **Input Validation**: Validate on input, ensuring backend safety
- **Fault Tolerance**: Service continues even when some providers fail with proper logging and error handling
- **Rate Limiting**: Token bucket algorithm prevents API quota exhaustion for OpenWeatherMap (60calls/min)
- **Global Support**: Accepts either city names and coordinates worldwide, even for OpenMeteo it will be able to take cityname now (By default only takes coordinates)
- **Weather Condition Standardization**: Converts different weather description from multi providers into a standard mapping list
- **Deployable Dockerfile**: Wrap up reuqired dependencies into portable docker image

## 📋 Prerequisites

- **Python 3.11+**
- **API Keys** from OpenWeatherMap and WeatherAPI
    - **OpenWeatherMap**: [https://openweathermap.org/api](https://openweathermap.org/api) (60 calls/minute free)
    - **WeatherAPI**: [https://www.weatherapi.com/signup.aspx](https://www.weatherapi.com/signup.aspx) (1M calls/month free)


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

# Install dependencies in virtual environment
pip install -r requirements.txt
```

### 3. Configure Environment with .env

```bash
# Copy environment template and update your API keys inside .env
cp .env.example .env

# Optional, you can update and create your own .env.dev, .env.uat and .env.prod with different configuration for each environment
```

**.env file:**
```env
# API Keys (Required)
OPENWEATHER_API_KEY=your_openweather_api_key_here
WEATHERAPI_KEY=your_weatherapi_key_here

(Optional)
# Logging level configuration
# Application Settings
# Cache TTL
# Timeout
# Rate Limiting
# Retry
# Connection Pool
```

### 4. Run the Application
**Option 1 - run with uvicorn**
```bash
# Development mode with auto-reload, using .env
uvicorn app.core.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2 - run with prepared scripts for specifed environment**
```bash
# Run with deployment scripts to specify environment
./scripts/run-dev.sh
./scripts/run-uat.sh
./scripts/run-prod.sh
```

### 5. API testing commands
**Option 1-Test on Swagger**
### View API documentation with authentication info [Recommended]
### open http://localhost:8000/docs

**Option 2-Test via curl/Postman**
```bash


# Health check (no authentication required)
curl http://localhost:8000/health

# Root endpoint (no authentication required)
curl http://localhost:8000/

# ============================================================================
# AUTHENTICATED ENDPOINTS (Bearer Token Required)
# ============================================================================

# Weather API - Normal User Access (Bearer Token: 123)
# 123 is normal user
# Get weather by city name
curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=Singapore"

# Get weather by coordinates  
curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=1.29,103.85"

# Test multiple locations
curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=New York"

curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=Tokyo"

curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=40.7128,-74.0060"

# ============================================================================
# ADMIN ENDPOINTS (Admin Bearer Token Required: abc)
# ============================================================================

# Get system configuration (Admin only)
# abc is admin user
curl -H "Authorization: Bearer abc" \
     "http://localhost:8000/api/v1/config"

# Clear cache (Admin only)
curl -X DELETE -H "Authorization: Bearer abc" \
     "http://localhost:8000/api/v1/cache"

# ============================================================================
# AUTHENTICATION TESTING
# ============================================================================

# Test without authentication (should fail with 401/403)
curl "http://localhost:8000/api/v1/weather?location=Singapore"

# Test with invalid token (should fail with 401/403)
curl -H "Authorization: Bearer invalid" \
     "http://localhost:8000/api/v1/weather?location=Singapore"

# Test normal user accessing admin endpoint (should fail with 403)
curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/config"

```

## 🐳 Docker Deployment

### Single Instance (Development)

```bash
# Build image on Dockerfile folder
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

### 🕥 Load Testing  

```bash
# Install hey for load testing
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Test single endpoint -> test on caching and async
hey -n 100 -c 10 "http://localhost:8000/api/v1/weather?location=Singapore"
```


## 🧪 Unit Test & Functional Test

```bash
# Run unit test with coverage and report
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Run funcitnoal test only
python -m pytest tests/test_functional.py -v
```
