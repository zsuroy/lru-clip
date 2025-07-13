"""
User model for authentication and user management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=True)  # Nullable for anonymous users
    email = Column(String(100), unique=True, index=True, nullable=True)  # Nullable for anonymous users
    hashed_password = Column(String(255), nullable=True)  # Nullable for anonymous users
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=False)  # Flag for anonymous users
    session_id = Column(String(64), unique=True, index=True, nullable=True)  # For anonymous session tracking
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # User preferences
    max_clips = Column(Integer, default=1000)  # LRU limit per user
    storage_quota = Column(Integer, default=1024*1024*1024)  # 1GB default
    
    # Relationships
    clips = relationship("Clip", back_populates="owner", cascade="all, delete-orphan")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
