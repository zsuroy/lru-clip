"""
LRU service for managing automatic cleanup of clips
"""

from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.clip import Clip
from app.models.user import User
from app.database import settings


class LRUService:
    """Service for LRU-based clip management"""
    
    def __init__(self):
        self.max_items_per_user = settings.lru_max_items_per_user
    
    def get_clips_for_cleanup(self, db: Session, user: User) -> List[Clip]:
        """Get clips that should be cleaned up based on LRU policy"""
        # Get all non-pinned clips for user, ordered by last access (oldest first)
        clips = db.query(Clip).filter(
            and_(
                Clip.owner_id == user.id,
                Clip.is_pinned == False
            )
        ).order_by(Clip.last_accessed).all()
        
        # If user has more clips than allowed, return excess clips for cleanup
        if len(clips) > user.max_clips:
            return clips[:len(clips) - user.max_clips]
        
        return []
    
    def cleanup_user_clips(self, db: Session, user: User) -> int:
        """Clean up excess clips for a user based on LRU policy"""
        clips_to_delete = self.get_clips_for_cleanup(db, user)
        
        deleted_count = 0
        for clip in clips_to_delete:
            # Additional check: don't delete recently created clips (less than 1 hour old)
            if clip.created_at > datetime.now(datetime.UTC) - timedelta(hours=1):
                continue
            
            db.delete(clip)
            deleted_count += 1
        
        if deleted_count > 0:
            db.commit()
        
        return deleted_count
    
    def cleanup_expired_clips(self, db: Session) -> int:
        """Clean up expired clips across all users"""
        now = datetime.now(datetime.UTC)
        expired_clips = db.query(Clip).filter(
            and_(
                Clip.expires_at.isnot(None),
                Clip.expires_at < now
            )
        ).all()
        
        deleted_count = len(expired_clips)
        for clip in expired_clips:
            db.delete(clip)
        
        if deleted_count > 0:
            db.commit()
        
        return deleted_count
    
    def get_user_storage_stats(self, db: Session, user: User) -> dict:
        """Get storage statistics for a user"""
        # Count clips
        total_clips = db.query(Clip).filter(Clip.owner_id == user.id).count()
        pinned_clips = db.query(Clip).filter(
            and_(Clip.owner_id == user.id, Clip.is_pinned == True)
        ).count()
        
        # Calculate storage usage (sum of file sizes)
        from app.models.file import File
        from sqlalchemy import func
        storage_used = db.query(func.sum(File.file_size)).filter(
            File.owner_id == user.id
        ).scalar() or 0
        
        return {
            "total_clips": total_clips,
            "pinned_clips": pinned_clips,
            "unpinned_clips": total_clips - pinned_clips,
            "max_clips": user.max_clips,
            "clips_available": max(0, user.max_clips - total_clips),
            "storage_used": storage_used,
            "storage_quota": user.storage_quota,
            "storage_available": max(0, user.storage_quota - storage_used),
            "storage_usage_percent": (storage_used / user.storage_quota * 100) if user.storage_quota > 0 else 0
        }
    
    def cleanup_anonymous_clips(self, db: Session) -> int:
        """Clean up clips from expired anonymous users"""
        from app.services.auth import auth_service

        # Clean up expired anonymous users (this will cascade delete their clips)
        deleted_users = auth_service.cleanup_expired_anonymous_users(db)

        # Also clean up anonymous clips that have expired individually
        expire_time = datetime.now(datetime.UTC) - timedelta(hours=settings.anonymous_clip_expire_hours)

        expired_clips = db.query(Clip).join(User).filter(
            and_(
                User.is_anonymous == True,
                Clip.created_at < expire_time,
                Clip.is_pinned == False  # Don't delete pinned clips even for anonymous users
            )
        ).all()

        deleted_clips = len(expired_clips)
        for clip in expired_clips:
            db.delete(clip)

        if deleted_clips > 0:
            db.commit()

        return deleted_clips

    def run_cleanup_for_all_users(self, db: Session) -> dict:
        """Run LRU cleanup for all users"""
        users = db.query(User).filter(User.is_active == True).all()

        total_deleted = 0
        users_cleaned = 0

        for user in users:
            deleted = self.cleanup_user_clips(db, user)
            if deleted > 0:
                total_deleted += deleted
                users_cleaned += 1

        # Also clean up expired clips
        expired_deleted = self.cleanup_expired_clips(db)

        # Clean up anonymous clips
        anonymous_deleted = self.cleanup_anonymous_clips(db)

        return {
            "users_processed": len(users),
            "users_cleaned": users_cleaned,
            "clips_deleted_lru": total_deleted,
            "clips_deleted_expired": expired_deleted,
            "clips_deleted_anonymous": anonymous_deleted,
            "total_deleted": total_deleted + expired_deleted + anonymous_deleted
        }


# Global instance
lru_service = LRUService()
