"""
Authentication and Authorization Module

This module provides role-based API key authentication for the Weather Data Aggregation Service.
It implements FastAPI security schemes using Bearer tokens with role-based access control.

The authentication system supports two user roles:
    - NORMAL: Standard user access (weather data retrieval)  
    - ADMIN: Administrative access (configuration, cache management)

Security Features:
    - Bearer token authentication via HTTP Authorization header
    - Role-based access control with hierarchical permissions
    - Integration with FastAPI dependency injection system
    - Swagger UI compatibility for interactive API documentation

Author: Li Beiji
Version: 1.0.0
"""
from enum import Enum
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .logger import get_logger

logger = get_logger(__name__)

class UserRole(Enum):
    """
    User role enumeration defining access levels within the system.
    
    Attributes:
        NORMAL: Standard user with read-only access to weather data
        ADMIN: Administrative user with full system access including configuration
    """
    NORMAL = "normal"
    ADMIN = "admin"

# API key to role mapping
API_KEY_ROLES = {
    "123": UserRole.NORMAL,
    "abc": UserRole.ADMIN,
}

# Shared security scheme for both authentication and Swagger UI
security = HTTPBearer()


def get_user_role(api_key: str) -> Optional[UserRole]:
    """
    Retrieve the user role associated with the provided API key.
    
    Args:
        api_key (str): The API key to look up
        
    Returns:
        Optional[UserRole]: The associated user role, or None if key is invalid
        
    Example:
        >>> get_user_role("123")
        UserRole.NORMAL
        >>> get_user_role("invalid")
        None
    """
    return API_KEY_ROLES.get(api_key, None)


# Authentication Functions for FastAPI Route Dependencies
async def verify_normal_user(
    token: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify that the provided token belongs to a normal user or admin.
    
    This function implements the authentication logic for endpoints that require
    normal user access or higher. It accepts tokens from both normal users and 
    administrators, providing hierarchical access control.
    
    Args:
        token (HTTPAuthorizationCredentials): Bearer token from request header
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: 401 Unauthorized if the API key is invalid
        
    Usage:
        @router.get("/weather")
        async def get_weather(api_key: str = Depends(verify_normal_user)):
            # Accessible to both normal users and admins
            pass
    """
    key = token.credentials
    
    # Validate API key exists in our authorized key registry
    if key not in API_KEY_ROLES:
        logger.warning(f"Invalid API key provided: {key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    logger.debug(f"Access granted: {key} -> {get_user_role(key).value}")
    return key

async def verify_admin_user(
    token: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify that the provided token belongs to an administrator.
    
    This function implements strict authentication logic for administrative endpoints.
    Only users with ADMIN role are granted access to protected administrative functions
    such as configuration management and cache operations.
    
    Args:
        token (HTTPAuthorizationCredentials): Bearer token from request header
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: 
            - 401 Unauthorized if the API key is invalid
            - 403 Forbidden if the user lacks administrative privileges
            
    Usage:
        @router.delete("/cache")
        def clear_cache(api_key: str = Depends(verify_admin_user)):
            # Accessible to admin users only
            pass
    """
    key = token.credentials
    
    if key not in API_KEY_ROLES:
        logger.warning(f"Invalid API key provided: {key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    user_role = get_user_role(key)
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    logger.debug(f"Admin access granted: {key}")
    return key
