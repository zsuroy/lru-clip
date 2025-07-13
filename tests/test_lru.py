"""
Tests for LRU service functionality
"""

import pytest
from datetime import datetime, timedelta
from app.services.lru import lru_service
from app.models.clip import Clip
from app.models.user import User


class TestLRUService:
    """Test LRU service functionality"""
    
    def test_get_user_storage_stats(self, db_session, test_user):
        """Test getting user storage statistics"""
        # Create some clips
        for i in range(5):
            clip = Clip(
                title=f"Clip {i}",
                content=f"Content {i}",
                owner_id=test_user.id,
                is_pinned=(i < 2)  # Pin first 2 clips
            )
            db_session.add(clip)
        
        db_session.commit()
        
        stats = lru_service.get_user_storage_stats(db_session, test_user)
        
        assert stats["total_clips"] == 5
        assert stats["pinned_clips"] == 2
        assert stats["unpinned_clips"] == 3
        assert stats["max_clips"] == test_user.max_clips
        assert stats["clips_available"] == test_user.max_clips - 5
    
    def test_cleanup_user_clips_within_limit(self, db_session, test_user):
        """Test cleanup when user is within clip limit"""
        # Create clips within limit
        for i in range(5):
            clip = Clip(
                title=f"Clip {i}",
                content=f"Content {i}",
                owner_id=test_user.id,
                created_at=datetime.utcnow() - timedelta(hours=2)  # Old enough to delete
            )
            db_session.add(clip)
        
        db_session.commit()
        
        deleted_count = lru_service.cleanup_user_clips(db_session, test_user)
        
        assert deleted_count == 0  # No clips should be deleted
        
        remaining_clips = db_session.query(Clip).filter(Clip.owner_id == test_user.id).count()
        assert remaining_clips == 5
    
    def test_cleanup_user_clips_over_limit(self, db_session, test_user):
        """Test cleanup when user exceeds clip limit"""
        # Set a low limit for testing
        test_user.max_clips = 3
        db_session.commit()
        
        # Create clips over the limit
        clips = []
        for i in range(5):
            clip = Clip(
                title=f"Clip {i}",
                content=f"Content {i}",
                owner_id=test_user.id,
                created_at=datetime.utcnow() - timedelta(hours=2),  # Old enough to delete
                last_accessed=datetime.utcnow() - timedelta(hours=i)  # Different access times
            )
            clips.append(clip)
            db_session.add(clip)
        
        db_session.commit()
        
        deleted_count = lru_service.cleanup_user_clips(db_session, test_user)
        
        assert deleted_count == 2  # Should delete 2 oldest clips
        
        remaining_clips = db_session.query(Clip).filter(Clip.owner_id == test_user.id).count()
        assert remaining_clips == 3
    
    def test_cleanup_respects_pinned_clips(self, db_session, test_user):
        """Test that pinned clips are not deleted during cleanup"""
        # Set a low limit for testing
        test_user.max_clips = 2
        db_session.commit()
        
        # Create clips, some pinned
        for i in range(4):
            clip = Clip(
                title=f"Clip {i}",
                content=f"Content {i}",
                owner_id=test_user.id,
                is_pinned=(i < 2),  # Pin first 2 clips
                created_at=datetime.utcnow() - timedelta(hours=2),
                last_accessed=datetime.utcnow() - timedelta(hours=i)
            )
            db_session.add(clip)
        
        db_session.commit()
        
        deleted_count = lru_service.cleanup_user_clips(db_session, test_user)
        
        assert deleted_count == 2  # Should delete 2 unpinned clips
        
        remaining_clips = db_session.query(Clip).filter(Clip.owner_id == test_user.id).all()
        assert len(remaining_clips) == 2
        
        # All remaining clips should be pinned
        for clip in remaining_clips:
            assert clip.is_pinned is True
    
    def test_cleanup_respects_recent_clips(self, db_session, test_user):
        """Test that recently created clips are not deleted"""
        # Set a low limit for testing
        test_user.max_clips = 2
        db_session.commit()
        
        # Create clips, some recent
        for i in range(4):
            clip = Clip(
                title=f"Clip {i}",
                content=f"Content {i}",
                owner_id=test_user.id,
                created_at=datetime.utcnow() - timedelta(minutes=30 if i < 2 else 120),  # First 2 are recent
                last_accessed=datetime.utcnow() - timedelta(hours=i)
            )
            db_session.add(clip)
        
        db_session.commit()
        
        deleted_count = lru_service.cleanup_user_clips(db_session, test_user)
        
        # Should only delete old clips, not recent ones
        assert deleted_count <= 2
        
        remaining_clips = db_session.query(Clip).filter(Clip.owner_id == test_user.id).count()
        assert remaining_clips >= 2
    
    def test_cleanup_expired_clips(self, db_session, test_user):
        """Test cleanup of expired clips"""
        # Create clips with different expiration times
        clips = []
        for i in range(3):
            expires_at = None
            if i == 0:
                expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
            elif i == 1:
                expires_at = datetime.utcnow() + timedelta(hours=1)  # Not expired
            # i == 2: No expiration
            
            clip = Clip(
                title=f"Clip {i}",
                content=f"Content {i}",
                owner_id=test_user.id,
                expires_at=expires_at
            )
            clips.append(clip)
            db_session.add(clip)
        
        db_session.commit()
        
        deleted_count = lru_service.cleanup_expired_clips(db_session)
        
        assert deleted_count == 1  # Only expired clip should be deleted
        
        remaining_clips = db_session.query(Clip).filter(Clip.owner_id == test_user.id).count()
        assert remaining_clips == 2
    
    def test_run_cleanup_for_all_users(self, db_session, test_user, test_admin_user):
        """Test running cleanup for all users"""
        # Set low limits for both users
        test_user.max_clips = 2
        test_admin_user.max_clips = 1
        db_session.commit()
        
        # Create clips for both users
        for user in [test_user, test_admin_user]:
            for i in range(3):
                clip = Clip(
                    title=f"Clip {i}",
                    content=f"Content {i}",
                    owner_id=user.id,
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    last_accessed=datetime.utcnow() - timedelta(hours=i)
                )
                db_session.add(clip)
        
        # Add an expired clip
        expired_clip = Clip(
            title="Expired",
            content="Expired content",
            owner_id=test_user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        db_session.add(expired_clip)
        
        db_session.commit()
        
        result = lru_service.run_cleanup_for_all_users(db_session)
        
        assert result["users_processed"] == 2
        assert result["users_cleaned"] == 2
        assert result["clips_deleted_lru"] == 3  # 1 from test_user, 2 from admin_user
        assert result["clips_deleted_expired"] == 1
        assert result["total_deleted"] == 4
