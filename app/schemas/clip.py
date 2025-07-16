"""
Clip-related Pydantic schemas
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.clip import ClipType, AccessLevel


class ClipBase(BaseModel):
    """Base clip schema"""
    title: Optional[str] = Field(None, max_length=200, description="Clip title")
    content: Optional[str] = Field(None, description="Clip content")
    clip_type: ClipType = Field(ClipType.TEXT, description="Type of clip")
    access_level: AccessLevel = Field(AccessLevel.PRIVATE, description="Access level")
    is_markdown: bool = Field(False, description="Whether content should be rendered as markdown")


class ClipCreate(ClipBase):
    """Schema for creating a clip"""
    password: Optional[str] = Field(None, description="Password for encrypted clips")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    file_ids: Optional[List[int]] = Field(None, description="IDs of files to associate with the clip")


class ClipUpdate(BaseModel):
    """Schema for updating a clip"""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    access_level: Optional[AccessLevel] = None
    password: Optional[str] = None
    is_pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None


class FileInfo(BaseModel):
    """File information for clip response"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ClipResponse(ClipBase):
    """Schema for clip response"""
    id: int
    share_token: Optional[str]
    is_pinned: bool
    access_count: int
    last_accessed: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    owner_id: int
    files: List[FileInfo] = []

    model_config = {
        "from_attributes": True
    }


class ClipListResponse(BaseModel):
    """Schema for clip list response"""
    clips: List[ClipResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ClipShareRequest(BaseModel):
    """Schema for sharing a clip"""
    access_level: AccessLevel
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class ClipAccessRequest(BaseModel):
    """Schema for accessing an encrypted clip"""
    password: str = Field(..., description="Password for encrypted clip")
