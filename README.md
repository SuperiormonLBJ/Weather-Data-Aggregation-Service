# Weather Data Aggregation Service

A professional RESTful API service that aggregates real-time weather data from 3 providers with intelligent fallback handling, rate limiting, RBAC and caching.

## 📑 Table of Contents

- [🌟 Features/Highlights](#-featureshighlights)
- [📋 Prerequisites](#-prerequisites)
- [🚀 Quick Start](#-quick-start)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Set Up Python Environment](#2-set-up-python-environment)
  - [3. Configure Environment with .env](#3-configure-environment-with-env)
  - [4. Run the Application](#4-run-the-application)
  - [5. API Testing Commands](#5-api-testing-commands)
- [🐳 Docker Deployment](#-docker-deployment)
- [🔧 Configuration Options](#-configuration-options)
- [🕥 Load Testing with Authentication](#-load-testing-with-authentication)
- [📚 API Documentation](#-api-documentation)
  - [🔐 Authentication & Authorization](#-authentication--authorization)
  - [📡 API Endpoints](#-api-endpoints)
  - [🚨 Error Responses](#-error-responses)
  - [🎯 Response Features](#-response-features)
  - [🔧 Integration Examples](#-integration-examples)
- [🧪 Unit Test & Functional Test](#-unit-test--functional-test)

---

## 🌟 Features/Highlights

- **Multi-Provider Aggregation**: Combines data from OpenWeatherMap, WeatherAPI.com, and Open-Meteo
- **Parallel Processing**: Concurrent Async API calls for optimal performance (1-2s total response time)
- **Persistent Session Management**: Reuse connection more efficiently and cut down waiting time
- **Smart Caching**: In-memory cache for fast read
- **Input Validation**: Validate on input, ensuring backend safety
- **Fault Tolerance**: Service continues even when some providers fail with proper logging and error handling
- **Rate Limiting**: Token bucket algorithm prevents API quota exhaustion for all providers
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

### 🕥 Load Testing with Authentication

```bash
# Install hey for load testing
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Test weather endpoint with bearer token authentication
hey -n 100 -c 10 \
    -H "Authorization: Bearer 123" \
    "http://localhost:8000/api/v1/weather?location=Singapore"

```

## 📚 API Documentation

### 🔐 Authentication & Authorization

The API uses **Bearer Token Authentication** with **Role-Based Access Control (RBAC)**:

| Role | Token | Access Level | Available Endpoints |
|------|-------|--------------|-------------------|
| **Normal User** | `123` | Weather data access | `/api/v1/weather` |
| **Admin** | `abc` | Full system access | All endpoints |

#### Authentication Header Format:
```
Authorization: Bearer <token>
```

### 📡 API Endpoints

#### **Public Endpoints** (No Authentication Required)

##### `GET /`
**Root endpoint**
- **Description**: API welcome message and basic info
- **Response**: JSON with service name and version

##### `GET /health`
**Health check endpoint**
- **Description**: Service health status
- **Response**: JSON with status and timestamp

##### `GET /docs`
**Interactive API Documentation**
- **Description**: Swagger UI for testing endpoints
- **Features**: Built-in authentication support

---

#### **Weather Endpoints** (Normal User Access Required)

##### `GET /api/v1/weather`
**Get aggregated weather data**

**Parameters:**
- `location` (required): City name or coordinates
  - City name: `"Singapore"`, `"New York"`, `"Tokyo"`
  - Coordinates: `"lat,lon"` format (e.g., `"1.29,103.85"`)

**Headers:**
```
Authorization: Bearer 123
```

**Example Requests:**
```bash
# City name
curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=Singapore"

# Coordinates
curl -H "Authorization: Bearer 123" \
     "http://localhost:8000/api/v1/weather?location=1.29,103.85"
```

**Response Format:**
```json
{
  "location": {
    "name": "Singapore",
    "latitude": 1.29,
    "longitude": 103.85,
    "country": "Singapore"
  },
  "conditions": {
    "temperature": 28.5,
    "humidity": 85,
    "pressure": 1013.2,
    "visibility": 10000,
    "uv_index": 7,
    "wind_speed": 5.2,
    "wind_direction": 180,
    "description": "Partly cloudy"
  },
  "sources": [
    "openweathermap",
    "weatherapi", 
    "openmeteo"
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "cached": false
}
```

---

#### **Admin Endpoints** (Admin Access Required)

##### `GET /api/v1/config`
**Get system configuration**

**Headers:**
```
Authorization: Bearer abc
```

**Example Request:**
```bash
curl -H "Authorization: Bearer abc" \
     "http://localhost:8000/api/v1/config"
```

**Response Format:**
```json
{
  "providers": {
    "openweathermap": {
      "enabled": true,
      "base_url": "https://api.openweathermap.org/data/2.5",
      "timeout": 10
    },
    "weatherapi": {
      "enabled": true,
      "base_url": "https://api.weatherapi.com/v1",
      "timeout": 10
    },
    "openmeteo": {
      "enabled": true,
      "base_url": "https://api.open-meteo.com/v1",
      "timeout": 10
    }
  },
  "cache_config": {
    "ttl_seconds": 300,
    "max_size": 1000
  },
  "retry_config": {
    "max_retries": 3,
    "backoff_factor": 1.5
  },
  "rate_limiting": {
    "requests_per_minute": 60,
    "burst_size": 10
  }
}
```

##### `DELETE /api/v1/cache`
**Clear system cache**

**Headers:**
```
Authorization: Bearer abc
```

**Example Request:**
```bash
curl -X DELETE -H "Authorization: Bearer abc" \
     "http://localhost:8000/api/v1/cache"
```

**Response Format:**
```json
{
  "message": "Cache cleared successfully",
  "cleared_entries": 45,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 🚨 Error Responses

#### Authentication Errors
```json
// 401 Unauthorized - Missing or invalid token
{
  "detail": "Not authenticated"
}

// 403 Forbidden - Insufficient permissions
{
  "detail": "Insufficient permissions for this operation"
}
```

#### Validation Errors
```json
// 400 Bad Request - Invalid location format
{
  "detail": "Invalid location format. Use city name or 'lat,lon' coordinates."
}

// 422 Unprocessable Entity - Missing required parameters
{
  "detail": [
    {
      "loc": ["query", "location"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### Service Errors
```json
// 503 Service Unavailable - All providers failed
{
  "detail": "Weather service temporarily unavailable. All providers failed.",
  "error_code": "ALL_PROVIDERS_FAILED"
}

// 429 Too Many Requests - Rate limit exceeded
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```


## 🧪 Unit Test & Functional Test

```bash
# Run unit test with coverage and report
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Run funcitnoal test only
python -m pytest tests/test_functional.py -v
```

