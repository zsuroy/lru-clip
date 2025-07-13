#!/usr/bin/env python3
"""
Database initialization script for CLIP.LRU
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import create_tables, drop_tables, settings
from app.models.user import User
from app.services.auth import auth_service
from app.database import SessionLocal


def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@clip.lru.cc",
            full_name="System Administrator",
            hashed_password=auth_service.get_password_hash("admin123"),
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main initialization function"""
    print("Initializing CLIP.LRU database...")
    print(f"Database URL: {settings.database_url}")
    
    try:
        # Create tables
        print("Creating database tables...")
        create_tables()
        print("Database tables created successfully")
        
        # Create storage directory
        os.makedirs(settings.storage_path, exist_ok=True)
        print(f"Storage directory created: {settings.storage_path}")
        
        # Create admin user
        print("Creating admin user...")
        create_admin_user()
        
        print("\nDatabase initialization completed successfully!")
        print("\nNext steps:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Login with admin credentials and change the password")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
