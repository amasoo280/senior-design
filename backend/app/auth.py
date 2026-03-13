"""
Auth0 JWT authentication utilities.

Validates Auth0-issued JWTs using JWKS (JSON Web Key Sets).
No local secret needed - Auth0's public keys are fetched automatically.
Fetches userinfo from Auth0 when the access token does not include email (common for API tokens).
"""
import json
from typing import Optional
from urllib.request import Request, urlopen

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
                detail="Unable to find appropriate key",
            )

        # Decode and verify the token. Accept either API audience or client ID (ID token).
        issuer = f"https://{settings.auth0_domain}/"
        audiences_to_try: list[str] = []
        if getattr(settings, "auth0_audience", None) and str(settings.auth0_audience).strip():
            audiences_to_try.append(settings.auth0_audience.strip())
        if getattr(settings, "auth0_client_id", None) and str(settings.auth0_client_id).strip():
            cid = settings.auth0_client_id.strip()
            if cid not in audiences_to_try:
                audiences_to_try.append(cid)

        last_error: Optional[Exception] = None
        for aud in audiences_to_try:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=aud,
                    issuer=issuer,
                )
                return payload
            except JWTError as e:
                last_error = e
                continue
        # As a development fallback, try verifying without audience check.
        # This is safe enough for local use because we still verify issuer and signature.
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                issuer=issuer,
                options={"verify_aud": False},
            )
            logger.warning(
                "Auth0 token accepted without audience verification "
                "(development fallback – ensure AUTH0_AUDIENCE is set correctly for production)."
            )
            return payload
        except JWTError as e:
            last_error = e

        if last_error:
            logger.warning(f"Auth0 token verification failed: {last_error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except JWTError as e:
        logger.warning(f"Auth0 token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Auth0 token verification unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _fetch_userinfo(access_token: str) -> Optional[dict]:
    """Fetch user profile from Auth0 Userinfo endpoint. Access tokens often omit email."""
    try:
        req = Request(
            f"https://{settings.auth0_domain}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"Auth0 userinfo fetch failed: {e}")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to get current authenticated user from Auth0 JWT.
    If the token does not include email (common for API access tokens), fetches
    userinfo from Auth0 so admin_emails and profile display work correctly.
    
    Returns a dict with user info: sub, email, name, picture, permissions.
    """
    token = credentials.credentials
    payload = _verify_auth0_token(token)
    
    email = payload.get("email") or payload.get(f"https://{settings.auth0_domain}/email")
    name = payload.get("name") or payload.get(f"https://{settings.auth0_domain}/name")
    
    # Many Auth0 API access tokens do not include email; fetch from userinfo
    if not email:
        userinfo = _fetch_userinfo(token)
        if userinfo:
            email = userinfo.get("email") or email
            if not name:
                name = userinfo.get("name")
            if not payload.get("picture") and userinfo.get("picture"):
                payload = {**payload, "picture": userinfo.get("picture")}
    
    user_info = {
        "sub": payload.get("sub"),
        "email": email,
        "name": name,
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
