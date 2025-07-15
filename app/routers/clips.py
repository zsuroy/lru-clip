"""
Clip management routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.clip import ClipType, AccessLevel
from app.schemas.clip import (
    ClipCreate, ClipUpdate, ClipResponse, ClipListResponse,
    ClipAccessRequest
)
from app.services.clip import clip_service
from app.services.lru import lru_service
from app.utils.auth import get_current_user_or_anonymous

router = APIRouter(prefix="/clips", tags=["Clips"])


@router.post("/", response_model=ClipResponse, status_code=status.HTTP_201_CREATED)
def create_clip(
    clip_create: ClipCreate,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Create a new clip"""
    # Check if user has reached clip limit
    stats = lru_service.get_user_storage_stats(db, current_user)
    if stats["clips_available"] <= 0:
        # Try to clean up old clips first
        deleted = lru_service.cleanup_user_clips(db, current_user)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Clip limit reached ({current_user.max_clips}). Please delete some clips or upgrade your account."
            )
    
    clip = clip_service.create_clip(db, clip_create, current_user)
    return ClipResponse.model_validate(clip)


@router.get("/", response_model=ClipListResponse)
def get_clips(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    clip_type: Optional[ClipType] = Query(None, description="Filter by clip type"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Get user's clips with pagination and filtering"""
    clips, total = clip_service.get_user_clips(
        db, current_user, 
        skip=(page - 1) * per_page, 
        limit=per_page,
        clip_type=clip_type,
        search=search
    )
    
    return ClipListResponse(
        clips=[ClipResponse.model_validate(clip) for clip in clips],
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
        has_prev=page > 1
    )


@router.get("/{clip_id}", response_model=ClipResponse)
def get_clip(
    clip_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Get a specific clip"""
    clip = clip_service.get_clip_by_id(db, clip_id, current_user)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found"
        )
    
    return ClipResponse.model_validate(clip)


@router.put("/{clip_id}", response_model=ClipResponse)
def update_clip(
    clip_id: int,
    clip_update: ClipUpdate,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Update a clip"""
    clip = clip_service.update_clip(db, clip_id, clip_update, current_user)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found"
        )
    
    return ClipResponse.model_validate(clip)


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clip(
    clip_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Delete a clip"""
    success = clip_service.delete_clip(db, clip_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found"
        )


@router.post("/{clip_id}/pin", response_model=ClipResponse)
def pin_clip(
    clip_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Pin a clip to prevent LRU cleanup"""
    clip = clip_service.pin_clip(db, clip_id, current_user, True)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found"
        )
    
    return ClipResponse.model_validate(clip)


@router.delete("/{clip_id}/pin", response_model=ClipResponse)
def unpin_clip(
    clip_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Unpin a clip"""
    clip = clip_service.pin_clip(db, clip_id, current_user, False)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found"
        )
    
    return ClipResponse.model_validate(clip)


@router.get("/shared/{share_token}", response_model=ClipResponse)
def get_shared_clip(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get a shared clip by token"""
    clip = clip_service.get_clip_by_share_token(db, share_token)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared clip not found or expired"
        )

    # If clip is encrypted, require password authentication
    if clip.access_level == AccessLevel.ENCRYPTED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password required for encrypted clip"
        )

    return ClipResponse.model_validate(clip)


@router.post("/shared/{share_token}/access", response_model=ClipResponse)
def access_encrypted_clip(
    share_token: str,
    access_request: ClipAccessRequest,
    db: Session = Depends(get_db)
):
    """Access an encrypted shared clip with password"""
    clip = clip_service.get_clip_by_share_token(db, share_token)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared clip not found or expired"
        )
    
    if clip.access_level != AccessLevel.ENCRYPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clip is not encrypted"
        )
    
    if not clip_service.verify_clip_password(access_request.password, clip.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    return ClipResponse.model_validate(clip)
