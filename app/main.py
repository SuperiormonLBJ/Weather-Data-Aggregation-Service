from fastapi import FastAPI
from app.routes import router as weather_router
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Weather Data Aggregation Service",
    description="A RESTful API that aggregates weather data from multiple providers",
    version="1.0.0"
)

# Include weather routes
app.include_router(weather_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Weather Data Aggregation Service", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
