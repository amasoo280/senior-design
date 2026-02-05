"""
Database initialization script.

Run this script to create the necessary database tables for OAuth authentication.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, engine
from app.models import Base, User, UserRole
from app.config import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

def main():
    """Initialize database tables."""
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print()
    
    # Show configuration
    print(f"Database: {settings.db_name}")
    print(f"Host: {settings.db_host}:{settings.db_port}")
    print(f"User: {settings.db_user}")
    print()
    
    # Test connection
    print("Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return 1
    
    print()
    
    # Create tables
    print("Creating database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Failed to create tables: {e}")
        return 1
    
    print()
    
    # Check if any users exist
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        print(f"Current user count: {user_count}")
        
        if user_count == 0:
            print()
            print("=" * 60)
            print("IMPORTANT: No users in database")
            print("=" * 60)
            print()
            print("To create an admin user, you have two options:")
            print()
            print("1. Set ADMIN_EMAILS in .env file:")
            print("   ADMIN_EMAILS=your-email@example.com")
            print("   Then log in with Google using that email.")
            print()
            print("2. Manually update the database:")
            print("   UPDATE users SET role='admin' WHERE email='your-email@example.com';")
            print()
    finally:
        db.close()
    
    print()
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Ensure your .env file has all required OAuth settings")
    print("2. Start the backend server: uvicorn main:app --reload")
    print("3. Start the frontend: cd frontend && npm run dev")
    print("4. Log in with Google OAuth")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
