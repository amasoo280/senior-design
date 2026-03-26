"""
Auth0 JWT authentication utilities.

Validates Auth0-issued JWTs using JWKS (JSON Web Key Sets).
No local secret needed - Auth0's public keys are fetched automatically.
Fetches userinfo from Auth0 when the access token does not include email (common for API tokens).
"""
import json
import time
from typing import Optional
from urllib.request import Request, urlopen

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.debug_agent_log import agent_log
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Security scheme for bearer token
security = HTTPBearer()

# Cache for JWKS
_jwks_cache = None

# Last-known email per Auth0 sub (userinfo/JWT); softens bursts of userinfo 429
_userinfo_email_by_sub: dict[str, tuple[float, str]] = {}
_USERINFO_EMAIL_CACHE_TTL_SEC = 900


def _cache_email_for_sub(sub: Optional[str], email: Optional[str]) -> None:
    if not sub or email is None:
        return
    em = str(email).strip()
    if not em:
        return
    _userinfo_email_by_sub[sub] = (
        time.monotonic() + _USERINFO_EMAIL_CACHE_TTL_SEC,
        em,
    )


def _cached_email_for_sub(sub: Optional[str]) -> Optional[str]:
    if not sub:
        return None
    hit = _userinfo_email_by_sub.get(sub)
    if not hit:
        return None
    expiry_mono, em = hit
    if time.monotonic() > expiry_mono:
        _userinfo_email_by_sub.pop(sub, None)
        return None
    return em


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

        # region agent log
        jwks_keys = jwks.get("keys", [])
        agent_log(
            "A",
            "auth.py:_verify_auth0_token",
            "jwt header vs jwks",
            {
                "header_kid": unverified_header.get("kid"),
                "header_alg": unverified_header.get("alg"),
                "jwks_key_count": len(jwks_keys),
                "auth0_domain_configured": bool(getattr(settings, "auth0_domain", None)),
            },
        )
        # endregion

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
            # region agent log
            agent_log(
                "A",
                "auth.py:_verify_auth0_token",
                "no rsa_key kid match",
                {"jwks_kids_sample": [k.get("kid") for k in jwks_keys[:5]]},
            )
            # endregion
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

        if last_error:
            # region agent log
            agent_log(
                "D",
                "auth.py:_verify_auth0_token",
                "jwt decode failed after rsa match",
                {"error_type": type(last_error).__name__},
            )
            # endregion
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

    sub = payload.get("sub")
    if isinstance(sub, str):
        if email:
            _cache_email_for_sub(sub, email)
        else:
            cached = _cached_email_for_sub(sub)
            if cached:
                email = cached
    
    user_info = {
        "sub": payload.get("sub"),
        "email": email,
        "name": name,
        "picture": payload.get("picture"),
        "permissions": payload.get("permissions", []),
    }

    # region agent log
    perms = user_info.get("permissions") or []
    em = (email or "").strip().lower()
    admin_list = settings.admin_emails or []
    agent_log(
        "B",
        "auth.py:get_current_user",
        "user claims snapshot",
        {
            "email_claim_present": bool(em),
            "permissions_count": len(perms) if isinstance(perms, list) else -1,
            "admin_emails_config_count": len(admin_list),
            "email_matches_admin_list": bool(
                em and admin_list and em in [e.lower().strip() for e in admin_list]
            ),
        },
    )
    # endregion

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


def user_email_matches_admin_allowlist(user: dict) -> bool:
    """True if user email is in settings.admin_emails. Missing or non-string email never matches."""
    admins = settings.admin_emails or []
    if not admins:
        return False
    raw = user.get("email")
    if raw is None or not isinstance(raw, str) or not raw.strip():
        return False
    normalized = raw.strip().lower()
    return normalized in {e.strip().lower() for e in admins if e and str(e).strip()}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency to require admin role.
    
    Checks Auth0 permissions for 'admin' role.
    Configure roles in Auth0 Dashboard > User Management > Roles.
    """
    permissions = user.get("permissions", [])
    admin_email_match = user_email_matches_admin_allowlist(user)
    is_admin = (
        "admin" in permissions
        or "admin:all" in permissions
        or admin_email_match
    )
    
    if not is_admin:
        logger.warning(
            f"Access denied for non-admin user: {user.get('email') or 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return user
