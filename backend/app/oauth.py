"""
Google OAuth 2.0 integration.
"""
from datetime import datetime
from typing import Optional
import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserRole
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Initialize OAuth client
oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


async def verify_google_token(token: str) -> Optional[dict]:
    """
    Verify Google ID token and return user info.
    
    Args:
        token: Google ID token from frontend
        
    Returns:
        User info dict with email, name, picture, sub (Google ID)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code != 200:
                logger.error(f"Google token verification failed: {response.status_code}")
                return None
                
            user_info = response.json()
            logger.info(f"Google token verified for user: {user_info.get('email')}")
            return user_info
            
    except Exception as e:
        logger.error(f"Error verifying Google token: {e}")
        return None


def get_or_create_user(db: Session, google_user_info: dict) -> User:
    """
    Get existing user or create new user from Google user info.
    
    Args:
        db: Database session
        google_user_info: User info from Google OAuth
        
    Returns:
        User object
    """
    google_id = google_user_info.get('sub')
    email = google_user_info.get('email')
    name = google_user_info.get('name')
    picture = google_user_info.get('picture')
    
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Invalid Google user info")
    
    # Try to find user by Google ID first
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if user:
        # Update last login and user info
        user.last_login = datetime.utcnow()
        user.name = name or user.name
        user.picture = picture or user.picture
        db.commit()
        db.refresh(user)
        logger.info(f"Existing user logged in: {email}")
        return user
    
    # Check if user with this email already exists (migrating from old auth)
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        # Update with Google ID
        user.google_id = google_id
        user.name = name or user.name
        user.picture = picture or user.picture
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        logger.info(f"Updated existing user with Google ID: {email}")
        return user
    
    # Create new user
    # First user with specific admin email becomes admin
    role = UserRole.ADMIN if is_admin_email(email) else UserRole.USER
    
    user = User(
        email=email,
        google_id=google_id,
        name=name,
        picture=picture,
        role=role,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Created new user: {email} (role: {role.value})")
    return user


def is_admin_email(email: str) -> bool:
    """
    Check if email should have admin role.
    
    You can customize this to:
    - Check against a list of admin emails in settings
    - Check email domain (e.g., @company.com)
    - Check against environment variable
    
    For now, we'll check against an environment variable.
    """
    admin_emails = settings.admin_emails
    if admin_emails:
        return email.lower() in [e.lower().strip() for e in admin_emails]
    
    # Default: no admins (you can manually set role in database)
    return False
