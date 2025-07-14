"""
Authentication routes
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, AnonymousSessionResponse
from app.services.auth import auth_service
from app.utils.auth import get_current_active_user, get_current_user_optional, require_authenticated_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Create user
    user = auth_service.create_user(db, user_create)
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    # Authenticate user
    user = auth_service.authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(require_authenticated_user)):
    """Get current user information (requires registered account)"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=Token)
def refresh_token(current_user = Depends(get_current_active_user)):
    """Refresh access token"""
    # Create new access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(current_user)
    )


@router.post("/anonymous", response_model=AnonymousSessionResponse, status_code=status.HTTP_201_CREATED)
def create_anonymous_session(db: Session = Depends(get_db)):
    """Create an anonymous session"""
    if not settings.allow_anonymous:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anonymous access is disabled"
        )

    # Create anonymous user
    user = auth_service.create_anonymous_user(db)

    return AnonymousSessionResponse(
        session_id=user.session_id,
        user=UserResponse.model_validate(user)
    )


@router.get("/status")
def get_auth_status(current_user = Depends(get_current_user_optional)):
    """Get current authentication status"""
    if not current_user:
        return {
            "authenticated": False,
            "anonymous_allowed": settings.allow_anonymous,
            "user": None
        }

    return {
        "authenticated": True,
        "anonymous_allowed": settings.allow_anonymous,
        "user": UserResponse.model_validate(current_user)
    }
