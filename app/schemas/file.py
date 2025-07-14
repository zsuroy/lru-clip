"""
File-related Pydantic schemas
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileResponse(BaseModel):
    """Schema for file response"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_hash: str
    is_image: bool
    is_video: bool
    is_audio: bool
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    download_count: int
    last_downloaded: Optional[datetime]
    created_at: datetime
    owner_id: int
    clip_id: Optional[int]

    model_config = {
        "from_attributes": True
    }


class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    file: FileResponse
    message: str = "File uploaded successfully"


class FileListResponse(BaseModel):
    """Schema for file list response"""
    files: list[FileResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
