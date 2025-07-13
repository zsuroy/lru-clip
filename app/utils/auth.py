"""
Authentication utilities and dependencies
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.models.user import User
from app.services.auth import auth_service


# Security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Verify token
    payload = auth_service.verify_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = auth_service.get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    x_session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user (authenticated or anonymous), returns None if no valid auth"""
    # Try JWT authentication first
    if credentials:
        try:
            payload = auth_service.verify_token(credentials.credentials)
            user_id = payload.get("sub")
            if user_id:
                user = auth_service.get_user_by_id(db, user_id=int(user_id))
                if user and user.is_active:
                    return user
        except:
            pass  # Invalid token, continue to anonymous check

    # Try anonymous session
    if x_session_id and settings.allow_anonymous:
        user = auth_service.get_user_by_session_id(db, x_session_id)
        if user and user.is_active:
            return user

    return None


def get_current_user_or_anonymous(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    x_session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user or create anonymous user if allowed"""
    # Try to get existing user
    user = get_current_user_optional(credentials, x_session_id, db)
    if user:
        return user

    # Create anonymous user if allowed
    if settings.allow_anonymous:
        return auth_service.create_anonymous_user(db)

    # No anonymous access allowed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_authenticated_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Require authenticated (non-anonymous) user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires a registered account"
        )

    return current_user
