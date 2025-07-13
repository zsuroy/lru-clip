"""
File management routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.file import FileResponse as FileResponseSchema, FileUploadResponse, FileListResponse
from app.services.file import file_service
from app.services.clip import clip_service
from app.utils.auth import get_current_active_user, get_current_user_or_anonymous


router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = FastAPIFile(...),
    clip_id: Optional[int] = Query(None, description="Associate with clip"),
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Upload a file"""
    # Validate clip if provided
    clip = None
    if clip_id:
        clip = clip_service.get_clip_by_id(db, clip_id, current_user)
        if not clip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clip not found"
            )
    
    # Upload file
    db_file = file_service.upload_file(db, file, current_user, clip)
    
    return FileUploadResponse(
        file=FileResponseSchema.from_orm(db_file),
        message="File uploaded successfully"
    )


@router.get("/", response_model=FileListResponse)
def get_files(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Get user's files with pagination"""
    files, total = file_service.get_user_files(
        db, current_user,
        skip=(page - 1) * per_page,
        limit=per_page
    )
    
    return FileListResponse(
        files=[FileResponseSchema.from_orm(f) for f in files],
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
        has_prev=page > 1
    )


@router.get("/{file_id}", response_model=FileResponseSchema)
def get_file_info(
    file_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Get file information"""
    file_obj = file_service.get_file_by_id(db, file_id, current_user)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponseSchema.from_orm(file_obj)


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Download a file"""
    file_obj = file_service.get_file_by_id(db, file_id, current_user)
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    file_path = file_service.get_file_path(file_obj)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=file_obj.original_filename,
        media_type=file_obj.mime_type
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    current_user = Depends(get_current_user_or_anonymous),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    success = file_service.delete_file(db, file_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
