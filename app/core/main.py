import os
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .routes import router as weather_router
from .logger import setup_logging, get_logger
from ..http.http_client import get_global_session, close_global_session

# Load environment
env_file = os.getenv('ENV_FILE', '.env')
load_dotenv(env_file)

# Setup logging first
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Weather Service")
    # Initialize global session
    await get_global_session()
    yield
    # Clean up global session
    await close_global_session()
    logger.info("Stopping Weather Service")

app = FastAPI(
    title="Weather Data Aggregation Service",
    description="Aggregates weather data from multiple providers with role-based authentication",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(weather_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Weather Data Aggregation Service", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
