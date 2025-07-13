"""
File service for handling file uploads and downloads
"""

import os
import hashlib
import shutil
from typing import Optional, List, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.models.file import File
from app.models.user import User
from app.models.clip import Clip
from app.database import settings


class FileService:
    """Service for managing file uploads and downloads"""
    
    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.max_file_size = settings.max_file_size
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, original_filename: str, file_hash: str) -> str:
        """Generate unique filename using hash"""
        file_ext = Path(original_filename).suffix
        return f"{file_hash}{file_ext}"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_file_info(self, file_path: Path, mime_type: str) -> dict:
        """Get file metadata"""
        info = {
            "is_image": mime_type.startswith("image/"),
            "is_video": mime_type.startswith("video/"),
            "is_audio": mime_type.startswith("audio/"),
            "width": None,
            "height": None,
            "duration": None
        }
        
        # TODO: Add image/video metadata extraction using PIL/ffmpeg
        # For now, just return basic info
        
        return info
    
    def upload_file(
        self,
        db: Session,
        file: UploadFile,
        user: User,
        clip: Optional[Clip] = None
    ) -> File:
        """Upload a file"""
        # Determine file size limit based on user type
        max_size = settings.anonymous_max_file_size if user.is_anonymous else self.max_file_size

        # Validate file size
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size} bytes"
            )
        
        # Create temporary file path
        temp_path = self.storage_path / f"temp_{file.filename}"
        
        try:
            # Save uploaded file temporarily
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(temp_path)
            
            # Check if file already exists (deduplication)
            existing_file = db.query(File).filter(File.file_hash == file_hash).first()
            if existing_file:
                # Remove temp file
                temp_path.unlink()
                
                # Create new file record pointing to existing file
                db_file = File(
                    filename=existing_file.filename,
                    original_filename=file.filename,
                    file_path=existing_file.file_path,
                    file_size=existing_file.file_size,
                    mime_type=file.content_type or "application/octet-stream",
                    file_hash=file_hash,
                    owner_id=user.id,
                    clip_id=clip.id if clip else None,
                    **self._get_file_info(Path(existing_file.file_path), file.content_type or "")
                )
            else:
                # Generate unique filename
                filename = self._generate_filename(file.filename, file_hash)
                final_path = self.storage_path / filename
                
                # Move temp file to final location
                temp_path.rename(final_path)
                
                # Get file size
                file_size = final_path.stat().st_size
                
                # Create file record
                db_file = File(
                    filename=filename,
                    original_filename=file.filename,
                    file_path=str(final_path),
                    file_size=file_size,
                    mime_type=file.content_type or "application/octet-stream",
                    file_hash=file_hash,
                    owner_id=user.id,
                    clip_id=clip.id if clip else None,
                    **self._get_file_info(final_path, file.content_type or "")
                )
            
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            
            return db_file
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )
    
    def get_file_by_id(self, db: Session, file_id: int, user: User) -> Optional[File]:
        """Get file by ID (only owner can access)"""
        file_obj = db.query(File).filter(
            File.id == file_id,
            File.owner_id == user.id
        ).first()
        
        if file_obj:
            file_obj.update_download()
            db.commit()
        
        return file_obj
    
    def get_file_path(self, file_obj: File) -> Path:
        """Get file path on disk"""
        return Path(file_obj.file_path)
    
    def delete_file(self, db: Session, file_id: int, user: User) -> bool:
        """Delete a file"""
        file_obj = db.query(File).filter(
            File.id == file_id,
            File.owner_id == user.id
        ).first()
        
        if not file_obj:
            return False
        
        # Check if other files reference the same physical file
        other_files = db.query(File).filter(
            File.file_hash == file_obj.file_hash,
            File.id != file_obj.id
        ).count()
        
        # Delete database record
        db.delete(file_obj)
        db.commit()
        
        # Delete physical file only if no other references exist
        if other_files == 0:
            file_path = Path(file_obj.file_path)
            if file_path.exists():
                file_path.unlink()
        
        return True
    
    def get_user_files(
        self, 
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[File], int]:
        """Get user's files with pagination"""
        query = db.query(File).filter(File.owner_id == user.id)
        
        total = query.count()
        files = query.order_by(File.created_at.desc()).offset(skip).limit(limit).all()
        
        return files, total


# Global instance
file_service = FileService()
