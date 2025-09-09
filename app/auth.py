"""
Simple API Key Authentication
"""
import os
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, APIKeyQuery, HTTPAuthorizationCredentials
from typing import Optional
from app.logger import get_logger

logger = get_logger(__name__)

# API key allowlist configuration from environment, defined by user in .env file
API_KEYS = set(os.getenv('API_KEYS', '').split(',')) if os.getenv('API_KEYS') else set()

# FastAPI Security schemes for Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)

# FastAPI-native authentication function for better Swagger integration
async def get_api_key(
    bearer_token: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> str:
    """
    FastAPI-native API key authentication that works well with Swagger UI.
    Tries Bearer token first, then query parameter.
    """
    
    # Extract API key from bearer token or query parameter
    key = None
    if bearer_token:
        key = bearer_token.credentials
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Use Authorization: Bearer <key> header or ?api_key=<key> parameter"
        )
    
    # Validate API key
    if key in API_KEYS:
        logger.debug("Valid API key provided")
        return key
    else:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )