"""
Admin routes for system management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.services.lru import lru_service
from app.services.auth import auth_service
from app.utils.auth import get_current_admin_user


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/cleanup/lru")
def run_lru_cleanup(
    admin_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Run LRU cleanup for all users (admin only)"""
    result = lru_service.run_cleanup_for_all_users(db)
    return {
        "message": "LRU cleanup completed",
        "result": result
    }


@router.get("/stats/storage")
def get_storage_stats(
    admin_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system storage statistics (admin only)"""
    from app.models.user import User
    from app.models.clip import Clip
    from app.models.file import File
    
    # Get basic counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_clips = db.query(Clip).count()
    total_files = db.query(File).count()
    
    # Get storage usage
    from sqlalchemy import func
    total_storage = db.query(func.sum(File.file_size)).scalar() or 0
    
    # Get top users by storage
    top_users = db.query(
        User.username,
        func.sum(File.file_size).label('storage_used')
    ).join(File).group_by(User.id).order_by(
        func.sum(File.file_size).desc()
    ).limit(10).all()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users
        },
        "clips": {
            "total": total_clips
        },
        "files": {
            "total": total_files,
            "total_storage_bytes": total_storage,
            "total_storage_mb": round(total_storage / (1024 * 1024), 2)
        },
        "top_users_by_storage": [
            {
                "username": user.username,
                "storage_used_bytes": user.storage_used,
                "storage_used_mb": round(user.storage_used / (1024 * 1024), 2)
            }
            for user in top_users
        ]
    }


@router.post("/cleanup/anonymous")
def cleanup_anonymous_users(
    admin_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Clean up expired anonymous users and their clips (admin only)"""
    deleted_users = auth_service.cleanup_expired_anonymous_users(db)
    deleted_clips = lru_service.cleanup_anonymous_clips(db)

    return {
        "message": "Anonymous user cleanup completed",
        "deleted_users": deleted_users,
        "deleted_clips": deleted_clips
    }


@router.get("/stats/anonymous")
def get_anonymous_stats(
    admin_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get anonymous user statistics (admin only)"""
    from app.models.user import User
    from app.models.clip import Clip
    from app.models.file import File

    # Get anonymous user counts
    total_anonymous = db.query(User).filter(User.is_anonymous == True).count()

    # Get anonymous clips and files
    anonymous_clips = db.query(Clip).join(User).filter(User.is_anonymous == True).count()
    anonymous_files = db.query(File).join(User).filter(User.is_anonymous == True).count()

    # Get anonymous storage usage
    anonymous_storage = db.query(func.sum(File.file_size)).join(User).filter(
        User.is_anonymous == True
    ).scalar() or 0

    return {
        "anonymous_users": {
            "total": total_anonymous,
            "settings": {
                "allow_anonymous": settings.allow_anonymous,
                "max_clips": settings.anonymous_max_clips,
                "max_file_size": settings.anonymous_max_file_size,
                "storage_quota": settings.anonymous_storage_quota,
                "expire_hours": settings.anonymous_clip_expire_hours
            }
        },
        "anonymous_content": {
            "clips": anonymous_clips,
            "files": anonymous_files,
            "storage_used_bytes": anonymous_storage,
            "storage_used_mb": round(anonymous_storage / (1024 * 1024), 2)
        }
    }
