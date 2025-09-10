"""
Role-based API Key Authentication (Bearer Token Only)
"""
from enum import Enum
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .logger import get_logger

logger = get_logger(__name__)

class UserRole(Enum):
    """User roles with different access levels"""
    NORMAL = "normal"
    ADMIN = "admin"

# API key to role mapping
API_KEY_ROLES = {
    "123": UserRole.NORMAL,
    "abc": UserRole.ADMIN,
}

# Shared security scheme for both authentication and Swagger UI
security = HTTPBearer()

def get_user_role(api_key: str) -> UserRole:
    """Get user role from API key"""
    return API_KEY_ROLES.get(api_key, None)

# Authentication functions for route dependencies
async def verify_normal_user(
    token: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify normal user or admin access"""
    key = token.credentials
    
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
    """Verify admin user access only"""
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
