from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .routes import router as weather_router
from .logger import setup_logging, get_logger

# Load environment
load_dotenv()

# Setup logging first
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Weather Service")
    yield
    logger.info("Stopping Weather Service")

app = FastAPI(
    title="Weather Data Aggregation Service",
    description="Aggregates weather data from multiple providers",
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
