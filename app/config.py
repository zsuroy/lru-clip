"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


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

    model_config = ConfigDict(env_file=".env")


settings = Settings()
