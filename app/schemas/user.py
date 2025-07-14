"""
User-related Pydantic schemas
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")


class UserCreate(UserBase):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password")


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_admin: bool
    is_anonymous: bool
    session_id: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    max_clips: int
    storage_quota: int

    model_config = {
        "from_attributes": True
    }


class UserUpdate(BaseModel):
    """Schema for user profile update"""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")


class AnonymousSessionCreate(BaseModel):
    """Schema for creating anonymous session"""
    pass


class AnonymousSessionResponse(BaseModel):
    """Schema for anonymous session response"""
    session_id: str
    user: UserResponse


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse
