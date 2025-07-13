"""
Authentication service for user management and JWT tokens
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.database import settings


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.jwt_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(datetime.UTC) + expires_delta
        else:
            expire = datetime.now(datetime.UTC) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password"""
        # Try to find user by username or email
        user = self.get_user_by_username(db, username)
        if not user:
            user = self.get_user_by_email(db, username)
        
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.now(datetime.UTC)
        db.commit()
        
        return user
    
    def create_user(self, db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if username already exists
        if self.get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if self.get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = self.get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user

    def create_anonymous_user(self, db: Session) -> User:
        """Create an anonymous user"""
        if not settings.allow_anonymous:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anonymous access is disabled"
            )

        # Generate unique session ID
        session_id = secrets.token_urlsafe(32)

        # Create anonymous user
        db_user = User(
            username=None,
            email=None,
            hashed_password=None,
            full_name=None,
            is_anonymous=True,
            session_id=session_id,
            max_clips=settings.anonymous_max_clips,
            storage_quota=settings.anonymous_storage_quota
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    def get_user_by_session_id(self, db: Session, session_id: str) -> Optional[User]:
        """Get anonymous user by session ID"""
        return db.query(User).filter(
            User.session_id == session_id,
            User.is_anonymous == True
        ).first()

    def cleanup_expired_anonymous_users(self, db: Session) -> int:
        """Clean up expired anonymous users"""
        expire_time = datetime.now(datetime.UTC) - timedelta(hours=settings.anonymous_clip_expire_hours)

        expired_users = db.query(User).filter(
            User.is_anonymous == True,
            User.created_at < expire_time
        ).all()

        deleted_count = len(expired_users)
        for user in expired_users:
            db.delete(user)

        if deleted_count > 0:
            db.commit()

        return deleted_count


# Global instance
auth_service = AuthService()
