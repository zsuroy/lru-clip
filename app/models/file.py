"""
File model for storing uploaded files
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class File(Base):
    """File model for storing uploaded files"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path on disk
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for deduplication
    
    # File metadata
    is_image = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    is_audio = Column(Boolean, default=False)
    width = Column(Integer, nullable=True)  # For images/videos
    height = Column(Integer, nullable=True)  # For images/videos
    duration = Column(Integer, nullable=True)  # For videos/audio (seconds)
    
    # Access tracking
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=True)  # Optional association with clip
    
    # Relationships
    owner = relationship("User", back_populates="files")
    clip = relationship("Clip", back_populates="files")
    
    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}', size={self.file_size})>"
    
    def update_download(self):
        """Update download statistics"""
        self.download_count += 1
        self.last_downloaded = func.now()
