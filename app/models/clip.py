"""
Clip model for storing clipboard content
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ClipType(enum.Enum):
    """Types of clip content"""
    TEXT = "text"
    MARKDOWN = "markdown"
    FILE = "file"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class AccessLevel(enum.Enum):
    """Access levels for clips"""
    PRIVATE = "private"      # Only owner can access
    PUBLIC = "public"        # Anyone with link can access
    ENCRYPTED = "encrypted"  # Requires password


class Clip(Base):
    """Clip model for storing clipboard content"""
    __tablename__ = "clips"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)  # For text/markdown content
    clip_type = Column(Enum(ClipType), nullable=False, default=ClipType.TEXT)
    access_level = Column(Enum(AccessLevel), nullable=False, default=AccessLevel.PRIVATE)
    
    # Security
    password_hash = Column(String(255), nullable=True)  # For encrypted clips
    share_token = Column(String(64), unique=True, index=True, nullable=True)  # For sharing
    
    # LRU management
    is_pinned = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="clips")
    files = relationship("File", back_populates="clip", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Clip(id={self.id}, title='{self.title}', type={self.clip_type.value})>"
    
    def update_access(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = func.now()
        self.access_count += 1
