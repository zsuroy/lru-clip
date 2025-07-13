"""
Database configuration and session management for CLIP.LRU
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    database_url: str = "mysql://root:password@localhost:3306/cliplru"
    secret_key: str = "your-secret-key-change-in-production"
    jwt_expire_minutes: int = 1440  # 24 hours
    storage_path: str = "./uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    lru_max_items_per_user: int = 1000
    lru_cleanup_interval: int = 3600  # 1 hour in seconds
    debug: bool = False

    # Anonymous user settings
    allow_anonymous: bool = True
    anonymous_max_clips: int = 100
    anonymous_max_file_size: int = 10 * 1024 * 1024  # 10MB for anonymous users
    anonymous_storage_quota: int = 100 * 1024 * 1024  # 100MB for anonymous users
    anonymous_clip_expire_hours: int = 24  # Anonymous clips expire after 24 hours

    class Config:
        env_file = ".env"


settings = Settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables (for testing)"""
    Base.metadata.drop_all(bind=engine)
