"""
Clip service for managing clipboard content
"""

import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.models.clip import Clip, AccessLevel, ClipType
from app.models.user import User
from app.schemas.clip import ClipCreate, ClipUpdate


class ClipService:
    """Service for managing clips"""
    
    def generate_share_token(self) -> str:
        """Generate a unique share token"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """Hash password for encrypted clips"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_clip_password(self, password: str, password_hash: str) -> bool:
        """Verify password for encrypted clips"""
        return self.hash_password(password) == password_hash
    
    def create_clip(self, db: Session, clip_create: ClipCreate, user: User) -> Clip:
        """Create a new clip"""
        # Generate share token if not private
        share_token = None
        if clip_create.access_level != AccessLevel.PRIVATE:
            share_token = self.generate_share_token()

        # Hash password if encrypted
        password_hash = None
        if clip_create.access_level == AccessLevel.ENCRYPTED and clip_create.password:
            password_hash = self.hash_password(clip_create.password)

        # Create clip
        db_clip = Clip(
            title=clip_create.title,
            content=clip_create.content,
            clip_type=clip_create.clip_type,
            access_level=clip_create.access_level,
            is_markdown=clip_create.is_markdown,
            password_hash=password_hash,
            share_token=share_token,
            expires_at=clip_create.expires_at,
            owner_id=user.id
        )

        db.add(db_clip)
        db.commit()
        db.refresh(db_clip)

        # Associate files if provided
        if clip_create.file_ids:
            from app.models.file import File
            for file_id in clip_create.file_ids:
                # Verify file belongs to user and update its clip_id
                file_obj = db.query(File).filter(
                    File.id == file_id,
                    File.owner_id == user.id
                ).first()
                if file_obj:
                    file_obj.clip_id = db_clip.id

            db.commit()
            db.refresh(db_clip)

        return db_clip
    
    def get_clip_by_id(self, db: Session, clip_id: int, user: User) -> Optional[Clip]:
        """Get clip by ID (only owner can access)"""
        clip = db.query(Clip).filter(
            and_(Clip.id == clip_id, Clip.owner_id == user.id)
        ).first()
        
        if clip:
            clip.update_access()
            db.commit()
        
        return clip
    
    def get_clip_by_share_token(self, db: Session, share_token: str) -> Optional[Clip]:
        """Get clip by share token (public access)"""
        clip = db.query(Clip).filter(Clip.share_token == share_token).first()
        
        if clip:
            # Check if expired
            if clip.expires_at and clip.expires_at < datetime.now(timezone.utc):
                return None
            
            clip.update_access()
            db.commit()
        
        return clip
    
    def get_user_clips(
        self, 
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 20,
        clip_type: Optional[ClipType] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Clip], int]:
        """Get user's clips with pagination and filtering"""
        if user.is_anonymous:
            query = db.query(Clip).filter(Clip.access_level == AccessLevel.PUBLIC)
        else:
            query = db.query(Clip).filter(Clip.owner_id == user.id)

        # Filter by type
        if clip_type:
            query = query.filter(Clip.clip_type == clip_type)
        
        # Search in title and content
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Clip.title.ilike(search_term),
                    Clip.content.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        clips = query.order_by(desc(Clip.last_accessed)).offset(skip).limit(limit).all()
        
        return clips, total
    
    def update_clip(self, db: Session, clip_id: int, clip_update: ClipUpdate, user: User) -> Optional[Clip]:
        """Update a clip"""
        clip = self.get_clip_by_id(db, clip_id, user)
        if not clip:
            return None
        
        # Update fields
        update_data = clip_update.model_dump(exclude_unset=True)
        
        # Handle password change for encrypted clips
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = self.hash_password(update_data["password"])
            del update_data["password"]
        
        # Handle access level change
        if "access_level" in update_data:
            if update_data["access_level"] == AccessLevel.PRIVATE:
                # Remove share token for private clips
                update_data["share_token"] = None
            elif clip.access_level == AccessLevel.PRIVATE:
                # Generate share token for newly public/encrypted clips
                update_data["share_token"] = self.generate_share_token()
        
        # Apply updates
        for field, value in update_data.items():
            setattr(clip, field, value)
        
        db.commit()
        db.refresh(clip)
        
        return clip
    
    def delete_clip(self, db: Session, clip_id: int, user: User) -> bool:
        """Delete a clip"""
        clip = self.get_clip_by_id(db, clip_id, user)
        if not clip:
            return False
        
        db.delete(clip)
        db.commit()
        
        return True
    
    def pin_clip(self, db: Session, clip_id: int, user: User, is_pinned: bool = True) -> Optional[Clip]:
        """Pin or unpin a clip"""
        clip = self.get_clip_by_id(db, clip_id, user)
        if not clip:
            return None
        
        clip.is_pinned = is_pinned
        db.commit()
        db.refresh(clip)
        
        return clip


# Global instance
clip_service = ClipService()
