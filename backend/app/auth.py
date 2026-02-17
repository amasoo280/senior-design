"""
Auth0 JWT authentication utilities.

Validates Auth0-issued JWTs using JWKS (JSON Web Key Sets).
No local secret needed - Auth0's public keys are fetched automatically.
"""
import json
from typing import Optional
from urllib.request import urlopen

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Security scheme for bearer token
security = HTTPBearer()

# Cache for JWKS
_jwks_cache = None


def _get_jwks() -> dict:
    """Fetch and cache Auth0's JWKS (JSON Web Key Set)."""
    global _jwks_cache
    if _jwks_cache is None:
        jwks_url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
        try:
            with urlopen(jwks_url) as response:
                _jwks_cache = json.loads(response.read())
            logger.info(f"Fetched JWKS from {jwks_url}")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch Auth0 public keys"
            )
    return _jwks_cache


def _verify_auth0_token(token: str) -> dict:
    """
    Verify an Auth0-issued JWT token.
    
    Returns the decoded token payload with user info.
    """
    try:
        jwks = _get_jwks()
        
        # Get the token header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the matching key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break
        
        if not rsa_key:
            logger.warning("Unable to find matching Auth0 signing key")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=f"https://{settings.auth0_domain}/"
        )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"Auth0 token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to get current authenticated user from Auth0 JWT.
    
    Usage:
        @app.get("/protected")
        def protected(user: dict = Depends(get_current_user)):
            ...
    
    Returns a dict with user info from the Auth0 token, including:
    - sub: Auth0 user ID
    - email: User's email
    - name: User's name (if available)
    - picture: User's profile picture URL (if available)
    """
    token = credentials.credentials
    payload = _verify_auth0_token(token)
    
    # Extract user info from Auth0 token claims
    user_info = {
        "sub": payload.get("sub"),
        "email": payload.get("email") or payload.get(f"https://{settings.auth0_domain}/email"),
        "name": payload.get("name") or payload.get(f"https://{settings.auth0_domain}/name"),
        "picture": payload.get("picture"),
        "permissions": payload.get("permissions", []),
    }
    
    return user_info


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[dict]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency to require admin role.
    
    Checks Auth0 permissions for 'admin' role.
    Configure roles in Auth0 Dashboard > User Management > Roles.
    """
    permissions = user.get("permissions", [])
    email = user.get("email", "unknown")
    
    # Check Auth0 permissions or admin emails from config
    is_admin = (
        "admin" in permissions
        or "admin:all" in permissions
        or (settings.admin_emails and email.lower() in [e.lower().strip() for e in settings.admin_emails])
    )
    
    if not is_admin:
        logger.warning(f"Access denied for non-admin user: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return user
